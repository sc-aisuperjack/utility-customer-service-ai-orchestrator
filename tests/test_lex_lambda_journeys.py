import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

HANDLER_PATH = ROOT / "aws" / "lambda" / "lex_fulfilment_handler.py"

spec = importlib.util.spec_from_file_location(
    "lex_fulfilment_handler",
    HANDLER_PATH,
)
lex_handler = importlib.util.module_from_spec(spec)
spec.loader.exec_module(lex_handler)


def make_lex_event(
    utterance: str,
    lex_intent_name: str,
    customer_id: str = "CUST001",
):
    return {
        "inputMode": "Speech",
        "inputTranscript": utterance,
        "sessionState": {
            "sessionAttributes": {
                "channel": "voice",
                "customer_id": customer_id,
            },
            "intent": {
                "name": lex_intent_name,
                "slots": {},
                "state": "InProgress",
            },
        },
    }


def get_attrs(result: dict) -> dict:
    return result["sessionState"]["sessionAttributes"]


def get_message(result: dict) -> str:
    return result["messages"][0]["content"]


def test_lex_high_bill_continues_self_service():
    event = make_lex_event(
        "My bill is much higher than usual.",
        "BillingHighIntent",
    )

    result = lex_handler.lambda_handler(event, context=None)
    attrs = get_attrs(result)
    message = get_message(result).lower()

    assert attrs["lex_intent"] == "BillingHighIntent"
    assert attrs["orchestrator_intent"] == "billing_high"
    assert attrs["handoff_required"] == "false"
    assert attrs["connect_next_action"] == "CONTINUE_SELF_SERVICE"

    assert "bill" in message
    assert "meter reading" in message or "billing period" in message


def test_lex_high_bill_with_vulnerability_transfers_to_priority_support():
    event = make_lex_event(
        "I can’t afford this bill and I have a medical condition.",
        "BillingHighIntent",
    )

    result = lex_handler.lambda_handler(event, context=None)
    attrs = get_attrs(result)
    message = get_message(result).lower()

    assert attrs["lex_intent"] == "BillingHighIntent"
    assert attrs["orchestrator_intent"] == "billing_high"
    assert attrs["risk_flags"] == "vulnerability_or_hardship"
    assert attrs["handoff_required"] == "true"
    assert attrs["handoff_queue"] == "priority_support"
    assert attrs["connect_next_action"] == "TRANSFER_TO_AGENT"

    assert "support" in message
    assert "specialist" in message or "adviser" in message


def test_lex_direct_debit_requires_financial_guardrail_but_continues_self_service():
    event = make_lex_event(
        "Can you change my Direct Debit date?",
        "ChangeDirectDebitIntent",
    )

    result = lex_handler.lambda_handler(event, context=None)
    attrs = get_attrs(result)
    message = get_message(result).lower()

    assert attrs["lex_intent"] == "ChangeDirectDebitIntent"
    assert attrs["orchestrator_intent"] == "direct_debit"
    assert attrs["risk_flags"] == "financial_or_high_impact_action"
    assert attrs["handoff_required"] == "false"
    assert attrs["connect_next_action"] == "CONTINUE_SELF_SERVICE"

    assert "direct debit" in message
    assert "confirmation" in message
    assert "has been changed" not in message


def test_lex_complaint_transfers_to_complaints_team():
    event = make_lex_event(
        "I want to make a complaint because nobody has fixed my billing issue.",
        "ComplaintIntent",
    )

    result = lex_handler.lambda_handler(event, context=None)
    attrs = get_attrs(result)
    message = get_message(result).lower()

    assert attrs["lex_intent"] == "ComplaintIntent"
    assert attrs["orchestrator_intent"] == "complaint"
    assert attrs["risk_flags"] == "complaint_or_escalation"
    assert attrs["handoff_required"] == "true"
    assert attrs["handoff_queue"] == "complaints_team"
    assert attrs["connect_next_action"] == "TRANSFER_TO_AGENT"

    assert "complaint" in message
    assert "confirm" in message
    assert "compensation" in message