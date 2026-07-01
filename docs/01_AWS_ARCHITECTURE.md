# AWS Architecture

Connect routes contacts. Lex understands intents and slots. Lambda fulfils deterministic logic. Bedrock generates grounded responses. Knowledge Bases retrieve trusted content. Guardrails block unsafe inputs/outputs. Contact Lens measures production performance.

Production path:
Connect -> Lex -> Lambda -> guardrails -> RAG -> tools -> Bedrock -> output validation -> response or handoff.

Start with bounded workflows for regulated journeys.
