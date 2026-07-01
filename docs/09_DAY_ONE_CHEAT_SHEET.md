# Day-One Cheat Sheet

60-second intro:
I built a local AWS-style utility customer-service AI lab with versioned prompts, local RAG, guardrails, mocked CRM/billing/meter/appointment/complaint tools, regression evals and optional Bedrock integration. I treated prompts as deployable artefacts, used golden test cases, and separated answer-only journeys from action-taking journeys with explicit confirmation and handoff rules.

Best lines:
- Prompts are behavioural code.
- Workflows first, agents second.
- RAG is not just vector search; it is policy-correct grounding.
- Voice needs separate constraints.
- Containment without safe resolution is vanity.
