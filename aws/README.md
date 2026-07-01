# AWS Integration Notes

Local lab to AWS mapping:

| Local lab | AWS equivalent |
|---|---|
| FastAPI `/chat` | Lambda/API Gateway or orchestration service |
| `app/llm.py` | Bedrock Runtime Converse API |
| `knowledge_base/` + `rag.py` | Bedrock Knowledge Bases / OpenSearch / Kendra |
| `guardrails.py` | Bedrock Guardrails + custom checks |
| `tools.py` | CRM/billing/meter/appointment APIs |
| `evals/` | CI eval job, Promptfoo, DeepEval, LangSmith/Langfuse |
| `aws/lambda/lex_fulfilment_handler.py` | Lex V2 fulfilment Lambda |
| `aws/connect/contact_flow_design.md` | Amazon Connect contact flow |

Deployment learning order:
1. Run local app.
2. Switch local app to Bedrock.
3. Package Lambda fulfilment.
4. Create Lex V2 bot.
5. Connect Lex to Lambda.
6. Add Amazon Connect flow.
7. Add Contact Lens/observability.
8. Add Bedrock Guardrails and Knowledge Base.
