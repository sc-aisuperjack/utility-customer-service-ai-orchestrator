# Two-Day Crash Plan

## Today: 5 hours
1. Read `docs/01_AWS_ARCHITECTURE.md` and `aws/README.md`.
2. Run the app locally.
3. Study `app/prompts/utility_assistant_v1.yaml`.
4. Test high bill, vulnerability, complaint, gas leak and prompt injection.
5. Run `pytest -q` and `python -m evals.run_evals`.

## Tomorrow: 12 hours
1. Trace high-bill workflow end to end.
2. Trace vulnerable-customer workflow end to end.
3. Trace complaint workflow end to end.
4. Read voice/IVR design.
5. Run optional LangGraph example.
6. Switch to Bedrock if AWS access is ready.
7. Read Lex/Lambda handler.
8. Read Amazon Connect handoff design.
9. Study CI/CD and release governance.
10. Practise the day-one explanation.

Goal sentence:
I built a local AWS-style utility customer-service AI lab with versioned prompts, RAG, guardrails, mocked CRM/billing tools, evals and optional Bedrock integration.
