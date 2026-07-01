# Bedrock Guardrails Design

Use Bedrock Guardrails plus custom app checks.

Input:
- PII
- prompt injection
- jailbreaks
- unsafe topics
- vulnerability/safety cues

Output:
- unsupported claims
- PII leakage
- high-impact action completion without tool confirmation
- groundedness failure
- toxic/abusive content

Business rules:
- vulnerability -> handoff
- safety emergency -> urgent support
- high-impact action -> confirmation
- billing answer -> retrieved policy or billing tool
