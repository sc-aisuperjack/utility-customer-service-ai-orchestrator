import json
from typing import List

from app.config import settings
from app.schemas import RetrievedDoc, ToolCallResult


def build_context(
    docs: List[RetrievedDoc],
    tool_results: List[ToolCallResult],
) -> str:
    """
    Build the grounding context passed to the model.

    In production, this would usually be assembled from:
    - retrieved knowledge articles
    - tool/API results
    - conversation state
    - policy constraints
    """
    parts: list[str] = []

    if docs:
        parts.append("Retrieved knowledge articles:")
        for d in docs:
            parts.append(
                f"[{d.policy_id}] {d.title} | "
                f"journey={d.journey_type} | "
                f"risk={d.risk_class} | "
                f"effective_date={d.effective_date}\n"
                f"{d.content}"
            )

    if tool_results:
        parts.append("Tool results:")
        for t in tool_results:
            parts.append(
                f"{t.tool_name} status={t.status}\n"
                f"{json.dumps(t.data, indent=2)}"
            )

    return "\n\n".join(parts)


def local_model_response(
    channel: str,
    message: str,
    intent: str,
    risks: List[str],
    docs: List[RetrievedDoc],
    tool_results: List[ToolCallResult],
) -> str:
    """
    Deterministic local stand-in for a real model.

    This keeps tests/evals stable without spending Bedrock tokens.
    Use MODEL_PROVIDER=bedrock only for integration testing.
    """
    voice = channel == "voice"

    if "prompt_attack" in risks:
        return (
            "I can’t help with that request. "
            "I can help with your energy account or connect you to support."
        )

    if "safety_emergency" in risks:
        if voice:
            return (
                "If you smell gas or feel unsafe, leave the property if you can do so safely "
                "and contact emergency support now. I’ll connect you to urgent support."
            )

        return (
            "If there may be a gas leak, carbon monoxide risk, fire, sparks, or immediate danger, "
            "leave the property if it is safe to do so and contact the appropriate emergency service immediately. "
            "I can also route this to urgent support."
        )

    if "vulnerability_or_hardship" in risks:
        if voice:
            return (
                "I can get you extra support. "
                "Because this may affect your energy needs, I’ll connect you to a specialist adviser."
            )

        return (
            "I can get you extra support with this. Because you mentioned something that may affect "
            "your energy needs or ability to pay, I should not keep this as a normal self-service journey. "
            "I can route you to a specialist adviser with the context included."
        )

    if intent == "complaint":
        return (
            "I’m sorry this has not been resolved. I can help summarise the issue and route it "
            "as a complaint, but I cannot promise an outcome or compensation. Please confirm the "
            "summary before I create anything."
        )

    if intent == "direct_debit":
        dd = next(
            (
                t.data
                for t in tool_results
                if t.tool_name == "get_direct_debit_summary"
                and t.status == "success"
            ),
            None,
        )

        if dd:
            return (
                f"Your current Direct Debit is active for £{dd['payment_amount']:.2f}, "
                f"taken on the {dd['payment_date']}. "
                "I can explain or collect a requested new date, but I would need explicit "
                "confirmation before any change is made."
            )

        return (
            "I can explain how to change your Direct Debit, but I would need to authenticate "
            "the account and confirm the new date before making any change."
        )

    if intent == "billing_high":
        billing = next(
            (
                t.data
                for t in tool_results
                if t.tool_name == "get_billing_summary"
                and t.status == "success"
            ),
            None,
        )

        if billing:
            reason_bits: list[str] = []

            if billing.get("meter_read_type") == "estimated":
                reason_bits.append("the bill is based on an estimated meter reading")

            if billing.get("billing_period_days", 0) > 35:
                reason_bits.append(
                    f"the billing period is longer than usual at {billing['billing_period_days']} days"
                )

            if billing.get("usage_change_percent", 0) > 20:
                reason_bits.append(
                    f"usage is around {billing['usage_change_percent']}% higher than the previous period"
                )

            reasons = (
                ", and ".join(reason_bits)
                if reason_bits
                else "the account data does not show one obvious cause"
            )

            if voice:
                return (
                    f"I can see {reasons}. "
                    "The safest next step is to submit an up-to-date meter reading or speak to billing support."
                )

            return (
                f"I checked the account context rather than guessing. The likely explanation is that {reasons}. "
                "The next safe step is to submit an up-to-date meter reading if the current bill is estimated, "
                "or route to billing support if the amount still looks wrong."
            )

        return (
            "I would need authenticated account and billing data to check your balance properly. "
            "I can explain common causes or connect you to billing support."
        )

    if intent == "meter_reading":
        return (
            "I can help with a meter reading. I’ll repeat the reading back and ask you to confirm "
            "before anything is submitted."
        )

    if intent == "appointment":
        appointments = next(
            (
                t.data
                for t in tool_results
                if t.tool_name == "get_appointments"
                and t.status == "success"
            ),
            None,
        )

        if appointments and appointments.get("appointments"):
            first = appointments["appointments"][0]
            return (
                f"I found an appointment for {first['type']} on {first['date']} "
                f"between {first['window']}. I would confirm before making any change."
            )

        return (
            "I can help with an engineer appointment, but I would need to check available slots "
            "and confirm before booking or changing anything."
        )

    if intent == "tariff":
        return (
            "I can explain tariff information from approved knowledge, but I should not recommend "
            "or complete a tariff switch without checking eligibility and confirming your choice."
        )

    return (
        "I can help with billing, meter readings, payments, appointments, complaints and account support. "
        "What would you like to do next?"
    )


def extract_bedrock_final_text(response: dict) -> str:
    """
    Extract only final customer-visible text from Bedrock Converse responses.

    Important:
    Some models, including reasoning-style models, can return content blocks like:
    - reasoningContent
    - reasoningText
    - text

    The app must only return final `text` blocks, never reasoningContent.
    """
    content = (
        response
        .get("output", {})
        .get("message", {})
        .get("content", [])
    )

    texts: list[str] = []

    for block in content:
        if isinstance(block, dict) and isinstance(block.get("text"), str):
            texts.append(block["text"])

    if texts:
        return "\n".join(texts)

    raise RuntimeError(f"No final text block found in Bedrock response: {response}")


def call_bedrock(
    system_prompt: str,
    channel: str,
    user_message: str,
    context: str,
) -> str:
    """
    Call Amazon Bedrock using the Converse API.

    Requires:
    - MODEL_PROVIDER=bedrock
    - AWS_REGION set in .env
    - BEDROCK_MODEL_ID set in .env
    - AWS credentials configured locally
    """
    import boto3

    client = boto3.client(
        "bedrock-runtime",
        region_name=settings.aws_region,
    )

    response = client.converse(
        modelId=settings.bedrock_model_id,
        system=[
            {
                "text": (
                    system_prompt
                    + "\n\nImportant output rule: return only the final customer-facing answer. "
                    "Do not include hidden reasoning, analysis, chain-of-thought, JSON unless requested, "
                    "or internal implementation details."
                )
            }
        ],
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "text": (
                            f"Channel: {channel}\n\n"
                            f"Grounding context and tool results:\n{context}\n\n"
                            f"Customer message:\n{user_message}\n\n"
                            "Return only the customer-facing answer."
                        )
                    }
                ],
            }
        ],
        inferenceConfig={
            "temperature": settings.temperature,
            "maxTokens": settings.max_tokens,
        },
    )

    return extract_bedrock_final_text(response)


def generate_answer(
    system_prompt: str,
    channel: str,
    message: str,
    intent: str,
    risks: List[str],
    docs: List[RetrievedDoc],
    tool_results: List[ToolCallResult],
) -> str:
    """
    Main model-provider switch.

    local:
      deterministic responses for tests and crash-course learning.

    bedrock:
      live AWS Bedrock model call using the same orchestration, RAG, tools and guardrails.
    """
    if settings.model_provider == "bedrock":
        return call_bedrock(
            system_prompt=system_prompt,
            channel=channel,
            user_message=message,
            context=build_context(docs, tool_results),
        )

    return local_model_response(
        channel=channel,
        message=message,
        intent=intent,
        risks=risks,
        docs=docs,
        tool_results=tool_results,
    )