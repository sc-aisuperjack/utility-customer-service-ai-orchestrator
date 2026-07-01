import json
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from app.main import app
from app.config import settings

client = TestClient(app)

PROMPT_VERSIONS = [
    "utility_assistant_v1",
    "utility_assistant_v2_voice_safe",
]

GOLDEN_CASES_PATH = ROOT / "evals" / "golden_cases.jsonl"
REPORTS_DIR = ROOT / "reports"
JSON_REPORT_PATH = REPORTS_DIR / "prompt_version_comparison.json"
MD_REPORT_PATH = REPORTS_DIR / "prompt_version_comparison.md"


def load_golden_cases() -> list[dict[str, Any]]:
    cases = []

    with GOLDEN_CASES_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()

            if not line:
                continue

            cases.append(json.loads(line))

    return cases


def answer_contains_any(answer: str, terms: list[str]) -> bool:
    low = answer.lower()
    return any(term.lower() in low for term in terms)


def voice_suitability(channel: str, answer: str) -> dict[str, Any]:
    """
    Lightweight voice-readiness check.

    For voice, answers should usually be short, clear and not overloaded.
    This is intentionally simple and deterministic for CI.
    """
    words = answer.split()
    word_count = len(words)

    if channel != "voice":
        return {
            "checked": False,
            "word_count": word_count,
            "ok": True,
            "reason": "Not a voice case.",
        }

    if word_count <= 55:
        return {
            "checked": True,
            "word_count": word_count,
            "ok": True,
            "reason": "Voice answer is concise.",
        }

    return {
        "checked": True,
        "word_count": word_count,
        "ok": False,
        "reason": "Voice answer is longer than 55 words.",
    }


def run_case(prompt_version: str, case: dict[str, Any]) -> dict[str, Any]:
    object.__setattr__(settings, "prompt_version", prompt_version)

    response = client.post(
        "/chat",
        json={
            "channel": case.get("channel", "chat"),
            "customer_id": case.get("customer_id", "CUST001"),
            "message": case["message"],
        },
    )

    status_ok = response.status_code == 200

    if not status_ok:
        return {
            "case_id": case["id"],
            "prompt_version": prompt_version,
            "passed": False,
            "status_code": response.status_code,
            "error": response.text,
        }

    body = response.json()
    decision = body["decision"]
    answer = body["answer_for_customer"]

    expected_intent = case.get("expected_intent")
    expected_handoff = case.get("requires_handoff")
    must_include_any = case.get("must_include_any", [])

    intent_ok = (
        expected_intent is None
        or decision["intent"] == expected_intent
    )

    handoff_ok = (
        expected_handoff is None
        or decision["requires_handoff"] is expected_handoff
    )

    include_ok = (
        not must_include_any
        or answer_contains_any(answer, must_include_any)
    )

    voice_check = voice_suitability(
        channel=case.get("channel", "chat"),
        answer=answer,
    )

    output_safety = body.get("observability", {}).get("output_safety", {})
    output_safety_ok = output_safety.get("ok", True)

    passed = all(
        [
            intent_ok,
            handoff_ok,
            include_ok,
            voice_check["ok"],
            output_safety_ok,
        ]
    )

    return {
        "case_id": case["id"],
        "prompt_version": prompt_version,
        "passed": passed,
        "status_code": response.status_code,
        "channel": body["channel"],
        "model_provider": body["model_provider"],
        "actual_prompt_version": body["prompt_version"],
        "expected_intent": expected_intent,
        "actual_intent": decision["intent"],
        "intent_ok": intent_ok,
        "expected_handoff": expected_handoff,
        "actual_handoff": decision["requires_handoff"],
        "handoff_ok": handoff_ok,
        "risk_flags": decision["risk_flags"],
        "recommended_next_action": decision["recommended_next_action"],
        "must_include_any": must_include_any,
        "include_ok": include_ok,
        "voice_check": voice_check,
        "retrieved_article_ids": decision.get("retrieved_article_ids", []),
        "tool_names": [
            t.get("tool_name")
            for t in decision.get("tool_results", [])
        ],
        "output_safety": output_safety,
        "answer_word_count": len(answer.split()),
        "answer": answer,
    }


def print_console_summary(results: list[dict[str, Any]]) -> None:
    print("\nPROMPT VERSION COMPARISON")
    print("=" * 120)

    header = (
        f"{'Prompt version':<34} "
        f"{'Case':<28} "
        f"{'Pass':<6} "
        f"{'Intent':<22} "
        f"{'Handoff':<8} "
        f"{'Words':<6} "
        f"{'Voice OK':<8}"
    )

    print(header)
    print("-" * len(header))

    for r in results:
        print(
            f"{r['prompt_version']:<34} "
            f"{r['case_id']:<28} "
            f"{str(r['passed']):<6} "
            f"{r.get('actual_intent', '-'):<22} "
            f"{str(r.get('actual_handoff', '-')):<8} "
            f"{str(r.get('answer_word_count', '-')):<6} "
            f"{str(r.get('voice_check', {}).get('ok', '-')):<8}"
        )

    print("\nSUMMARY")
    print("=" * 120)

    by_version: dict[str, list[dict[str, Any]]] = {}

    for r in results:
        by_version.setdefault(r["prompt_version"], []).append(r)

    for version, version_results in by_version.items():
        passed = sum(1 for r in version_results if r["passed"])
        total = len(version_results)
        print(f"{version}: {passed}/{total} cases passed")


def write_reports(results: list[dict[str, Any]]) -> None:
    REPORTS_DIR.mkdir(exist_ok=True)

    JSON_REPORT_PATH.write_text(
        json.dumps(results, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# Prompt Version Comparison Report",
        "",
        "This report compares configured assistant instruction versions against the same golden evaluation cases.",
        "",
        "The comparison checks:",
        "",
        "- expected intent",
        "- expected handoff decision",
        "- required answer content",
        "- voice-answer length",
        "- output safety result",
        "- retrieved articles",
        "- tool calls",
        "",
        "## Summary",
        "",
        "| Prompt version | Passed | Total |",
        "|---|---:|---:|",
    ]

    by_version: dict[str, list[dict[str, Any]]] = {}

    for r in results:
        by_version.setdefault(r["prompt_version"], []).append(r)

    for version, version_results in by_version.items():
        passed = sum(1 for r in version_results if r["passed"])
        total = len(version_results)
        lines.append(f"| `{version}` | {passed} | {total} |")

    lines.extend(
        [
            "",
            "## Case Results",
            "",
            "| Prompt version | Case | Passed | Intent | Handoff | Risk flags | Words | Voice OK |",
            "|---|---|---:|---|---:|---|---:|---:|",
        ]
    )

    for r in results:
        risk_flags = ", ".join(r.get("risk_flags", [])) or "none"
        lines.append(
            f"| `{r['prompt_version']}` "
            f"| `{r['case_id']}` "
            f"| {r['passed']} "
            f"| `{r.get('actual_intent', '-')}` "
            f"| {r.get('actual_handoff', '-')} "
            f"| {risk_flags} "
            f"| {r.get('answer_word_count', '-')} "
            f"| {r.get('voice_check', {}).get('ok', '-')} |"
        )

    lines.extend(
        [
            "",
            "## Notes",
            "",
            "Local deterministic mode is designed to keep tests stable. In this mode, prompt-version comparison validates release-governance plumbing and safety behaviour. When a live model provider is enabled, the same report can be used to compare language and response-quality differences between prompt versions.",
            "",
        ]
    )

    MD_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    original_prompt_version = settings.prompt_version
    cases = load_golden_cases()

    results = []

    try:
        for prompt_version in PROMPT_VERSIONS:
            for case in cases:
                results.append(run_case(prompt_version, case))
    finally:
        object.__setattr__(settings, "prompt_version", original_prompt_version)

    print_console_summary(results)
    write_reports(results)

    failed = [r for r in results if not r["passed"]]

    print("\nREPORTS WRITTEN")
    print("=" * 120)
    print(JSON_REPORT_PATH)
    print(MD_REPORT_PATH)

    if failed:
        print("\nFAILED CASES")
        print("=" * 120)

        for r in failed:
            print(
                f"{r['prompt_version']} / {r['case_id']} failed "
                f"| intent_ok={r.get('intent_ok')} "
                f"| handoff_ok={r.get('handoff_ok')} "
                f"| include_ok={r.get('include_ok')} "
                f"| voice_ok={r.get('voice_check', {}).get('ok')} "
                f"| output_safety_ok={r.get('output_safety', {}).get('ok', True)}"
            )

        raise SystemExit(1)

    print("\nAll prompt versions passed the comparison gate.")


if __name__ == "__main__":
    main()