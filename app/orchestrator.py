from uuid import uuid4
from typing import List

from app.config import settings
from app.prompt_loader import load_prompt
from app.guardrails import apply_input_guardrails, output_safety_check, normalise_text
from app.rag import retrieve
from app.llm import generate_answer
from app.schemas import ChatRequest, ChatResponse, AssistantDecision, ToolCallResult
from app import tools


def classify_intent(message: str, risks: List[str]) -> str:
    low = normalise_text(message)

    if "safety_emergency" in risks:
        return "safety_emergency"

    if "complaint_or_escalation" in risks:
        return "complaint"

    if "direct debit" in low:
        return "direct_debit"

    if (
        "prepayment" in low
        or "top up" in low
        or "top-up" in low
        or "topup" in low
        or "prepay" in low
    ):
        return "prepayment"

    if "meter" in low or "reading" in low or "smart" in low:
        return "meter_reading"

    if (
        "engineer" in low
        or "appointment" in low
        or "boiler" in low
        or "repair" in low
    ):
        return "appointment"

    if "tariff" in low or "switch" in low or "fixed" in low or "variable" in low:
        return "tariff"

    if "move" in low or "moving home" in low or "new address" in low:
        return "moving_home"

    if (
        "bill" in low
        or "balance" in low
        or "charge" in low
        or "expensive" in low
        or "higher" in low
        or "cost" in low
        or "pay" in low
    ):
        return "billing_high"

    if "vulnerability_or_hardship" in risks:
        return "vulnerability_support"

    return "general"


def run_tools(
    intent: str,
    customer_id: str,
    risks: List[str],
    message: str,
) -> List[ToolCallResult]:
    results: List[ToolCallResult] = []

    profile_result = tools.get_customer_profile(customer_id)
    results.append(profile_result)

    profile = profile_result.data or {}
    account_id = profile.get("account_id") if profile.get("authenticated") else None

    if intent in {"billing_high", "prepayment", "tariff"} and "prompt_attack" not in risks:
        results.append(tools.get_billing_summary(account_id))

    if intent == "direct_debit" and "prompt_attack" not in risks:
        results.append(tools.get_direct_debit_summary(account_id))

    if intent == "appointment" and "prompt_attack" not in risks:
        results.append(tools.get_appointments(account_id))

    if intent == "complaint" and "prompt_attack" not in risks:
        results.append(tools.create_complaint(account_id, summary=message[:500]))

    if "vulnerability_or_hardship" in risks:
        results.append(
            tools.handoff_to_agent(
                "priority_support",
                "vulnerability_or_hardship",
                message[:500],
                {
                    "intent": intent,
                    "customer_id": customer_id,
                },
            )
        )

    if "safety_emergency" in risks:
        results.append(
            tools.handoff_to_agent(
                "emergency_support",
                "safety_emergency",
                message[:500],
                {
                    "intent": intent,
                    "customer_id": customer_id,
                },
            )
        )

    return results


def should_handoff(
    intent: str,
    risks: List[str],
    tool_results: List[ToolCallResult],
) -> tuple[bool, str | None]:
    if "prompt_attack" in risks:
        return True, "Prompt injection or hidden-instruction request."

    if "safety_emergency" in risks:
        return True, "Potential gas/electricity safety emergency."

    if "vulnerability_or_hardship" in risks:
        return (
            True,
            "Customer mentioned vulnerability, hardship, medical dependency, or risk of self-disconnection.",
        )

    if intent == "complaint":
        return True, "Complaint or escalation intent."

    for tr in tool_results:
        if tr.status in {"handoff_required", "needs_authentication"}:
            data = tr.data or {}
            return True, data.get("reason") or tr.error or "Tool requires handoff/authentication."

    return False, None


def handle_chat(req: ChatRequest) -> ChatResponse:
    prompt = load_prompt(settings.prompt_version)

    guard = apply_input_guardrails(req.message)

    intent = classify_intent(guard.redacted, guard.risks)

    docs = retrieve(
        guard.redacted,
        top_k=settings.max_retrieved_docs,
    )

    tool_results = run_tools(
        intent,
        req.customer_id,
        guard.risks,
        guard.redacted,
    )

    requires_handoff, handoff_reason = should_handoff(
        intent,
        guard.risks,
        tool_results,
    )

    answer = generate_answer(
        prompt["system"],
        req.channel,
        guard.redacted,
        intent,
        guard.risks,
        docs,
        tool_results,
    )

    output_check = output_safety_check(
        answer,
        [d.policy_id for d in docs],
    )

    if not output_check["ok"]:
        answer = (
            "I cannot safely confirm that from the available information. "
            "I can connect you to a specialist adviser."
        )
        requires_handoff = True
        handoff_reason = "Output safety check failed: " + ",".join(output_check["flags"])

    decision = AssistantDecision(
        intent=intent,
        risk_flags=guard.risks,
        requires_authentication=any(
            t.status == "needs_authentication" for t in tool_results
        ),
        requires_handoff=requires_handoff,
        handoff_reason=handoff_reason,
        recommended_next_action="handoff" if requires_handoff else "answer_or_continue",
        tool_results=tool_results,
        retrieved_article_ids=[d.policy_id for d in docs],
    )

    return ChatResponse(
        conversation_id=req.conversation_id or str(uuid4()),
        prompt_version=prompt["id"],
        model_provider=settings.model_provider,
        channel=req.channel,
        customer_id=req.customer_id,
        answer_for_customer=answer,
        decision=decision,
        retrieved_docs=docs,
        redacted_user_message=guard.redacted,
        observability={
            "prompt_version": prompt["id"],
            "model_provider": settings.model_provider,
            "intent": intent,
            "risk_flags": guard.risks,
            "retrieved_article_ids": [d.policy_id for d in docs],
            "tool_names": [t.tool_name for t in tool_results],
            "output_safety": output_check,
        },
    )