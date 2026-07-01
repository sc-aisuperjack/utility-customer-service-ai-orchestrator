import re
from dataclasses import dataclass
from typing import List, Dict

EMAIL_RE = re.compile(r"[\w\.-]+@[\w\.-]+\.\w+")
PHONE_RE = re.compile(r"\b(?:\+44|0)\s?\d{3,5}[\s-]?\d{3}[\s-]?\d{3,4}\b")
POSTCODE_RE = re.compile(r"\b[A-Z]{1,2}\d[A-Z\d]?\s?\d[A-Z]{2}\b", re.I)
ACCOUNT_RE = re.compile(
    r"\b(?:account|acct|customer|reference|ref)\s*(?:number|no|id)?\s*[:#]?\s*[A-Z0-9]{6,14}\b",
    re.I,
)
CARD_RE = re.compile(r"\b(?:\d[ -]*?){13,16}\b")


PROMPT_ATTACK_TERMS = [
    "ignore previous instructions",
    "ignore all previous instructions",
    "reveal your system prompt",
    "developer message",
    "system message",
    "jailbreak",
    "do anything now",
    "dan mode",
    "forget your rules",
    "print your hidden prompt",
    "bypass safety",
]


VULNERABILITY_TERMS = [
    # General vulnerability
    "vulnerable",
    "medically vulnerable",
    "priority services",
    "priority services register",
    "psr",

    # Medical / disability
    "disabled",
    "disability",
    "medical condition",
    "medical equipment",
    "oxygen",
    "dialysis",
    "insulin",
    "life support",
    "terminal illness",
    "blind",
    "deaf",
    "dementia",
    "autism",
    "mobility",
    "carer",

    # Age / household vulnerability
    "elderly",
    "pensioner",
    "baby",
    "newborn",
    "young child",
    "pregnant",

    # Mental health
    "mental health",
    "anxiety",
    "depression",

    # Hardship / affordability
    "can't afford",
    "cannot afford",
    "cant afford",
    "can't afford this bill",
    "cannot afford this bill",
    "can't pay",
    "cannot pay",
    "cant pay",
    "struggling to pay",
    "unable to pay",
    "payment difficulty",
    "financial difficulty",
    "debt",
    "arrears",

    # Energy-specific hardship / risk
    "self disconnect",
    "self-disconnect",
    "self disconnection",
    "self-disconnection",
    "no heating",
    "no electricity",
    "prepayment meter",
    "prepay",
    "warrant",
]


COMPLAINT_TERMS = [
    "complain",
    "complaint",
    "ombudsman",
    "formal complaint",
    "not happy",
    "unacceptable",
    "escalate this",
    "poor service",
    "you haven't resolved",
    "haven't resolved",
    "deadlock letter",
]


SAFETY_TERMS = [
    "gas leak",
    "smell gas",
    "carbon monoxide",
    "co alarm",
    "sparks",
    "electrical fire",
    "burning smell",
    "boiler leaking",
    "danger",
    "emergency",
    "unsafe",
]


PAYMENT_RISK_TERMS = [
    "refund",
    "payment plan",
    "direct debit",
    "bank details",
    "card number",
    "compensation",
    "credit",
    "debit",
    "repayment",
]


@dataclass
class GuardrailResult:
    original: str
    redacted: str
    risks: List[str]
    blocked: bool = False
    block_reason: str | None = None


def normalise_text(text: str) -> str:
    """
    Normalise common punctuation so keyword checks catch both:
    - can't
    - can’t
    """
    return (
        text.lower()
        .replace("’", "'")
        .replace("‘", "'")
        .replace("“", '"')
        .replace("”", '"')
        .replace("–", "-")
        .replace("—", "-")
    )


def redact_pii(text: str) -> str:
    text = EMAIL_RE.sub("<EMAIL>", text)
    text = PHONE_RE.sub("<PHONE>", text)
    text = POSTCODE_RE.sub("<POSTCODE>", text)
    text = ACCOUNT_RE.sub("<ACCOUNT_REF>", text)
    text = CARD_RE.sub("<CARD_NUMBER>", text)
    return text


def _contains_any(text: str, terms: List[str]) -> bool:
    low = normalise_text(text)
    return any(term in low for term in terms)


def detect_risks(text: str) -> List[str]:
    risks: List[str] = []

    if (
        EMAIL_RE.search(text)
        or PHONE_RE.search(text)
        or POSTCODE_RE.search(text)
        or ACCOUNT_RE.search(text)
        or CARD_RE.search(text)
    ):
        risks.append("pii_present")

    if _contains_any(text, PROMPT_ATTACK_TERMS):
        risks.append("prompt_attack")

    if _contains_any(text, VULNERABILITY_TERMS):
        risks.append("vulnerability_or_hardship")

    if _contains_any(text, COMPLAINT_TERMS):
        risks.append("complaint_or_escalation")

    if _contains_any(text, SAFETY_TERMS):
        risks.append("safety_emergency")

    if _contains_any(text, PAYMENT_RISK_TERMS):
        risks.append("financial_or_high_impact_action")

    return list(dict.fromkeys(risks))


def apply_input_guardrails(text: str) -> GuardrailResult:
    risks = detect_risks(text)
    blocked = "prompt_attack" in risks

    return GuardrailResult(
        original=text,
        redacted=redact_pii(text),
        risks=risks,
        blocked=blocked,
        block_reason=(
            "Potential prompt injection or hidden-instruction request."
            if blocked
            else None
        ),
    )


def output_safety_check(answer: str, retrieved_article_ids: List[str]) -> Dict:
    flags = []
    low = normalise_text(answer)

    for phrase in [
        "guaranteed compensation",
        "your refund has been issued",
        "your payment plan is active",
        "your tariff has been changed",
        "we will disconnect",
    ]:
        if phrase in low:
            flags.append(f"unsafe_promise:{phrase}")

    if "bill" in low and not retrieved_article_ids:
        flags.append("billing_answer_without_retrieval")

    return {"ok": not flags, "flags": flags}