import json
from pathlib import Path
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)
CASES = Path(__file__).parent / "golden_cases.jsonl"

def load_cases():
    for line in CASES.read_text(encoding="utf-8").splitlines():
        if line.strip():
            yield json.loads(line)

def assert_case(case):
    res = client.post("/chat", json={"channel": case["channel"], "customer_id": case["customer_id"], "message": case["message"]})
    assert res.status_code == 200, res.text
    data = res.json()
    answer = data["answer_for_customer"].lower()
    failures = []
    if data["decision"]["intent"] != case["expected_intent"]:
        failures.append(f"intent expected {case['expected_intent']} got {data['decision']['intent']}")
    if "requires_handoff" in case and data["decision"]["requires_handoff"] != case["requires_handoff"]:
        failures.append(f"handoff expected {case['requires_handoff']} got {data['decision']['requires_handoff']}")
    if case.get("must_include_any") and not any(t.lower() in answer for t in case["must_include_any"]):
        failures.append(f"answer did not contain any of {case['must_include_any']}")
    for forbidden in case.get("must_not_include", []):
        if forbidden.lower() in answer:
            failures.append(f"answer contained forbidden phrase: {forbidden}")
    return data, failures

def main():
    total = failed = 0
    for case in load_cases():
        total += 1
        data, failures = assert_case(case)
        if failures:
            failed += 1
            print(f"❌ {case['id']}")
            for f in failures:
                print(f"   - {f}")
            print(f"   answer: {data['answer_for_customer']}")
        else:
            print(f"✅ {case['id']}")
    print(f"\n{total - failed}/{total} cases passed")
    if failed:
        raise SystemExit(1)

if __name__ == "__main__":
    main()
