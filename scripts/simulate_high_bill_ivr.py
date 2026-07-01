import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


CANDIDATE_ENDPOINTS = [
    "/assist",
    "/api/assist",
    "/api/v1/assist",
    "/chat",
    "/api/chat",
    "/api/v1/chat",
    "/orchestrate",
    "/api/orchestrate",
    "/api/v1/orchestrate",
]


def say(step: str, text: str):
    print("\n" + "=" * 80)
    print(step)
    print("=" * 80)
    print(text)


def print_routes():
    say("AVAILABLE FASTAPI ROUTES", "")

    for route in app.routes:
        methods = getattr(route, "methods", None)
        path = getattr(route, "path", None)

        if methods and path:
            print(f"{sorted(methods)} {path}")


def call_assistant(message: str, customer_id: str = "CUST001"):
    """
    Simulates Lex/Lambda sending a voice-channel request into the app.
    Tries common endpoint names until it finds the correct one.
    """
    payload = {
        "channel": "voice",
        "customer_id": customer_id,
        "message": message,
    }

    last_error = None

    for endpoint in CANDIDATE_ENDPOINTS:
        response = client.post(endpoint, json=payload)

        if response.status_code == 200:
            print(f"\nUsing endpoint: {endpoint}")
            return response.json()

        last_error = {
            "endpoint": endpoint,
            "status_code": response.status_code,
            "body": response.text,
        }

        if response.status_code != 404:
            print(f"\nEndpoint exists but request failed: {endpoint}")
            print("Status:", response.status_code)
            print(response.text)
            raise RuntimeError("Assistant call failed with non-404 error")

    print("\nNo candidate endpoint worked.")
    print("Last error:")
    print(json.dumps(last_error, indent=2))

    raise RuntimeError("Could not find assistant endpoint")


def main():
    print_routes()

    say(
        "CONNECT",
        "Welcome to British Gas. How can I help you today?"
    )

    # customer_message = "My bill is much higher than usual."
    # customer_message = "I can’t afford this bill and I have a medical condition."
    # customer_message = "Can you change my Direct Debit date?"
    customer_message = "I want to make a complaint because nobody has fixed my billing issue."

    say(
        "CUSTOMER",
        customer_message
    )

    say(
        "LEX",
        "Customer utterance captured. Sending to Lambda fulfilment."
    )

    result = call_assistant(customer_message)

    decision = result.get("decision", {})

    say(
        "LAMBDA → ORCHESTRATOR RESULT",
        json.dumps(
            {
                "model_provider": result.get("model_provider"),
                "prompt_version": result.get("prompt_version"),
                "intent": decision.get("intent"),
                "risk_flags": decision.get("risk_flags"),
                "requires_authentication": decision.get("requires_authentication"),
                "requires_handoff": decision.get("requires_handoff"),
                "retrieved_article_ids": decision.get("retrieved_article_ids"),
                "tool_results": [
                    {
                        "tool_name": t.get("tool_name"),
                        "status": t.get("status"),
                    }
                    for t in decision.get("tool_results", [])
                ],
            },
            indent=2,
        ),
    )

    say(
        "BOT VOICE RESPONSE",
        result.get("answer_for_customer", "")
    )

    say(
        "CONNECT NEXT STEP",
        "If the customer is unhappy, vulnerable, or needs account changes, route to a human adviser."
    )


if __name__ == "__main__":
    main()