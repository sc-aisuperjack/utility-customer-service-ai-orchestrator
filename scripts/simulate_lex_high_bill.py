import json
import sys
import importlib.util
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
    lex_intent_name: str = "BillingHighIntent",
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


def print_result(title: str, event: dict, result: dict):
    attrs = result.get("sessionState", {}).get("sessionAttributes", {})
    message = result.get("messages", [{}])[0].get("content", "")

    print("\n" + "=" * 90)
    print(title)
    print("=" * 90)

    print("\nCUSTOMER SAID:")
    print(event["inputTranscript"])

    print("\nLEX RESPONSE TO CUSTOMER:")
    print(message)

    print("\nSESSION ATTRIBUTES FOR CONNECT:")
    print(
        json.dumps(
            {
                "lex_intent": attrs.get("lex_intent"),
                "orchestrator_intent": attrs.get("orchestrator_intent"),
                "risk_flags": attrs.get("risk_flags"),
                "handoff_required": attrs.get("handoff_required"),
                "handoff_queue": attrs.get("handoff_queue"),
                "connect_next_action": attrs.get("connect_next_action"),
                "handoff_reason": attrs.get("handoff_reason"),
                "prompt_version": attrs.get("prompt_version"),
                "model_provider": attrs.get("model_provider"),
            },
            indent=2,
        )
    )


def run_case(title: str, utterance: str, lex_intent_name: str = "BillingHighIntent"):
    event = make_lex_event(
        utterance=utterance,
        lex_intent_name=lex_intent_name,
    )

    result = lex_handler.lambda_handler(event, context=None)

    print_result(title, event, result)


def main():
    run_case(
        "NORMAL HIGH BILL IVR JOURNEY",
        "My bill is much higher than usual.",
        "BillingHighIntent",
    )

    run_case(
        "HIGH BILL + VULNERABILITY IVR JOURNEY",
        "I can’t afford this bill and I have a medical condition.",
        "BillingHighIntent",
    )

    run_case(
        "DIRECT DEBIT IVR JOURNEY",
        "Can you change my Direct Debit date?",
        "ChangeDirectDebitIntent",
    )

    run_case(
        "COMPLAINT IVR JOURNEY",
        "I want to make a complaint because nobody has fixed my billing issue.",
        "ComplaintIntent",
    )


if __name__ == "__main__":
    main()