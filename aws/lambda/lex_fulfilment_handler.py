import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Allows this file to run locally from aws/lambda while importing the app package.
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

from app.schemas import ChatRequest
from app.orchestrator import handle_chat


def close(
    intent_name: str,
    message: str,
    session_attributes: Optional[Dict[str, str]] = None,
    state: str = "Fulfilled",
) -> Dict[str, Any]:
    """
    Lex V2 Close response.

    Amazon Connect can inspect sessionAttributes after the Lex bot returns.
    For example:
      handoff_required=true
      handoff_queue=priority_support
    """
    return {
        "sessionState": {
            "sessionAttributes": session_attributes or {},
            "dialogAction": {
                "type": "Close",
            },
            "intent": {
                "name": intent_name,
                "state": state,
            },
        },
        "messages": [
            {
                "contentType": "PlainText",
                "content": message,
            }
        ],
    }


def get_session_attributes(event: Dict[str, Any]) -> Dict[str, str]:
    session_state = event.get("sessionState", {}) or {}
    attrs = session_state.get("sessionAttributes", {}) or {}

    # Lex session attributes should be string values.
    return {str(k): str(v) for k, v in attrs.items()}


def get_intent_name(event: Dict[str, Any]) -> str:
    session_state = event.get("sessionState", {}) or {}
    intent = session_state.get("intent", {}) or {}
    return intent.get("name", "FallbackIntent")


def get_transcript(event: Dict[str, Any]) -> str:
    """
    In a real Lex voice journey, inputTranscript is the text Lex heard
    from the caller after speech-to-text.
    """
    transcript = event.get("inputTranscript", "") or ""

    if transcript.strip():
        return transcript.strip()

    return "Customer did not provide an utterance."


def derive_handoff_queue(risk_flags: list[str], intent: str) -> str:
    """
    This is the value Amazon Connect could use to route the call.
    """
    if "safety_emergency" in risk_flags:
        return "emergency_support"

    if "vulnerability_or_hardship" in risk_flags:
        return "priority_support"

    if intent == "complaint" or "complaint_or_escalation" in risk_flags:
        return "complaints_team"

    if "financial_or_high_impact_action" in risk_flags:
        return "billing_support"

    return "general_support"


def lambda_handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    transcript = get_transcript(event)
    intent_name = get_intent_name(event)
    session_attrs = get_session_attributes(event)

    chat_response = handle_chat(
        ChatRequest(
            channel=session_attrs.get("channel", "voice"),
            customer_id=session_attrs.get("customer_id", "ANON"),
            message=transcript,
            conversation_id=session_attrs.get("conversation_id"),
        )
    )

    decision = chat_response.decision
    risk_flags = decision.risk_flags or []

    session_attrs["conversation_id"] = chat_response.conversation_id
    session_attrs["orchestrator_intent"] = decision.intent
    session_attrs["lex_intent"] = intent_name
    session_attrs["risk_flags"] = ",".join(risk_flags)
    session_attrs["handoff_required"] = str(decision.requires_handoff).lower()
    session_attrs["recommended_next_action"] = decision.recommended_next_action
    session_attrs["model_provider"] = chat_response.model_provider
    session_attrs["prompt_version"] = chat_response.prompt_version

    if decision.handoff_reason:
        session_attrs["handoff_reason"] = decision.handoff_reason

    if decision.requires_handoff:
        session_attrs["handoff_queue"] = derive_handoff_queue(
            risk_flags=risk_flags,
            intent=decision.intent,
        )
        session_attrs["connect_next_action"] = "TRANSFER_TO_AGENT"
    else:
        session_attrs["handoff_queue"] = ""
        session_attrs["connect_next_action"] = "CONTINUE_SELF_SERVICE"

    return close(
        intent_name=intent_name,
        message=chat_response.answer_for_customer,
        session_attributes=session_attrs,
        state="Fulfilled",
    )