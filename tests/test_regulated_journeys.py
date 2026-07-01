from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_direct_debit_requires_financial_guardrail_and_confirmation():
    response = client.post(
        "/chat",
        json={
            "channel": "voice",
            "customer_id": "CUST001",
            "message": "Can you change my Direct Debit date?",
        },
    )

    assert response.status_code == 200

    body = response.json()
    decision = body["decision"]

    assert decision["intent"] == "direct_debit"
    assert "financial_or_high_impact_action" in decision["risk_flags"]

    answer = body["answer_for_customer"].lower()

    assert "direct debit" in answer
    assert "confirmation" in answer
    assert "has been changed" not in answer
    assert "changed your direct debit" not in answer


def test_complaint_requires_handoff_and_confirmation():
    response = client.post(
        "/chat",
        json={
            "channel": "voice",
            "customer_id": "CUST001",
            "message": "I want to make a complaint because nobody has fixed my billing issue.",
        },
    )

    assert response.status_code == 200

    body = response.json()
    decision = body["decision"]

    assert decision["intent"] == "complaint"
    assert "complaint_or_escalation" in decision["risk_flags"]
    assert decision["requires_handoff"] is True
    assert decision["recommended_next_action"] == "handoff"

    answer = body["answer_for_customer"].lower()

    assert "complaint" in answer
    assert "confirm" in answer
    assert "cannot promise" in answer or "can't promise" in answer