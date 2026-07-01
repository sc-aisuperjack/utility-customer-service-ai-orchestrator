from pathlib import Path
from typing import List, Dict, Any
import re
import math
from app.schemas import RetrievedDoc
from app.config import settings

KB_DIR = Path(__file__).parent / "knowledge_base"

def parse_doc(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    meta = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            raw_meta = parts[1]
            body = parts[2].strip()
            for line in raw_meta.splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    return {
        "policy_id": meta.get("policy_id", path.stem),
        "title": meta.get("title", path.stem.replace("_", " ").title()),
        "journey_type": meta.get("journey_type", "general"),
        "risk_class": meta.get("risk_class", "low"),
        "effective_date": meta.get("effective_date", "2026-01-01"),
        "source": str(path.relative_to(KB_DIR)),
        "content": body,
    }

def load_docs() -> List[Dict[str, Any]]:
    return [parse_doc(p) for p in sorted(KB_DIR.rglob("*.md"))]

def tokenize(text: str) -> List[str]:
    return [t.lower() for t in re.findall(r"[a-zA-Z0-9]{3,}", text)]

def retrieve(query: str, top_k: int | None = None) -> List[RetrievedDoc]:
    top_k = top_k or settings.max_retrieved_docs
    docs = load_docs()
    q_tokens = tokenize(query)
    q_set = set(q_tokens)
    if not q_tokens:
        return []

    journey_boosts = {
        "bill": "billing", "billing": "billing", "balance": "billing", "charge": "billing",
        "meter": "metering", "reading": "metering", "smart": "metering",
        "complaint": "complaints", "ombudsman": "complaints",
        "prepayment": "prepayment", "prepay": "prepayment", "topup": "prepayment",
        "boiler": "appointments", "engineer": "appointments", "repair": "appointments",
        "move": "moving_home", "address": "moving_home",
        "disabled": "vulnerability", "medical": "vulnerability", "vulnerable": "vulnerability",
        "tariff": "tariffs", "switch": "tariffs",
        "gas": "safety", "leak": "safety", "carbon": "safety",
    }

    scored = []
    for doc in docs:
        content = f"{doc['title']} {doc['journey_type']} {doc['risk_class']} {doc['content']}"
        d_tokens = tokenize(content)
        d_set = set(d_tokens)
        overlap = len(q_set & d_set)
        phrase_score = 0
        low_query = query.lower()
        low_content = content.lower()
        for phrase in ["high bill", "meter reading", "prepayment meter", "priority services", "gas leak", "formal complaint", "payment plan"]:
            if phrase in low_query and phrase in low_content:
                phrase_score += 5
        metadata_score = sum(2 for t in q_tokens if journey_boosts.get(t) == doc["journey_type"])
        risk_score = 2 if doc["risk_class"] == "high" and any(t in low_query for t in ["medical", "vulnerable", "complaint", "gas leak", "prepayment", "no heating", "cannot afford"]) else 0
        score = (overlap + phrase_score + metadata_score + risk_score) / math.log(len(d_tokens) + 10)
        if score > 0:
            scored.append((score, doc))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [
        RetrievedDoc(
            policy_id=doc["policy_id"],
            title=doc["title"],
            journey_type=doc["journey_type"],
            risk_class=doc["risk_class"],
            effective_date=doc["effective_date"],
            source=doc["source"],
            score=round(float(score), 4),
            content=doc["content"],
        )
        for score, doc in scored[:top_k]
    ]
