# Responsible Contact-Centre AI Lab

A local-first AI orchestration lab for building and testing safe customer-service assistant behaviour in a regulated utility-style environment.

This project is a fictional demo. It is not affiliated with any real energy supplier, employer, client, recruitment process or public-sector body.

The lab demonstrates how a customer-service AI system can combine:

- versioned assistant instructions
- voice-style and chat-style response design
- retrieval from approved local knowledge articles
- mocked CRM, billing, meter, appointment, payment and complaint tools
- PII detection and redaction
- prompt-injection protection
- emergency, complaint, financial-action and vulnerable-customer guardrails
- workflow orchestration
- optional AWS Bedrock model provider
- Amazon Lex-style Lambda fulfilment
- Amazon Connect-style handoff routing
- regression tests and golden-case evaluations
- CI/CD starter workflow
- journey safety reporting

The default mode is fully local and deterministic, so the project can be run and tested without using paid model APIs.



## What this project simulates

The project simulates a responsible customer-service assistant for an example utility provider.

It can handle journeys such as:

- high bill explanation
- high bill plus hardship or medical vulnerability
- Direct Debit date enquiry
- meter reading support
- engineer appointment enquiry
- complaint escalation
- emergency safety escalation
- prompt-injection blocking
- anonymous account/balance request handling

The goal is not to build a perfect chatbot. The goal is to demonstrate how regulated AI workflows can be structured, tested and released safely.



## Architecture


Customer voice/chat
  ↓
Amazon Connect-style contact flow / web chat
  ↓
Lex-style intent capture / routing
  ↓
Lambda / FastAPI orchestration
  ↓
Input guardrails
  ↓
Retrieval from approved knowledge
  ↓
Tool calls to mocked CRM/billing/meter/appointment/complaint systems
  ↓
Local deterministic model or optional Bedrock model
  ↓
Output safety checks
  ↓
Customer response or human handoff
  ↓
Observability, evaluations and release governance


## Key behaviours

### Normal high bill

The assistant explains likely causes using account context, such as estimated readings, longer billing periods or increased usage.

### High bill plus vulnerability or hardship

The assistant does not continue as normal self-service. It flags vulnerability or hardship and routes to priority support.

### Direct Debit change

The assistant may explain the current Direct Debit status and collect a requested date, but it must not claim the payment instruction has been changed without explicit confirmation and a trusted tool result.

### Complaint

The assistant can summarise the issue and prepare escalation, but it must not promise compensation or a specific outcome.

### Emergency

The assistant gives short safety-first guidance and routes to urgent support.

### Prompt injection

The assistant blocks attempts to reveal hidden instructions or bypass safety rules.



## Quick start

```bash
cd responsible-contact-centre-ai-lab

python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate

pip install -r requirements.txt
cp .env.example .env

uvicorn app.main:app --reload --port 8001
```

Open:

```text
http://localhost:8001
```

API docs:

```text
http://localhost:8001/docs
```

---

## Windows PowerShell quick start

```powershell
cd D:\pythondev\responsible-contact-centre-ai-lab

python -m venv .venv
.venv\Scripts\activate

pip install -r requirements.txt
copy .env.example .env

uvicorn app.main:app --reload --port 8001
```

---

## Run tests and evaluations

```bash
python -m pytest
python -m evals.run_evals
```

Expected result:

```text
All tests pass
All golden eval cases pass
```

---

## Run journey simulations

### Customer journey safety report

```bash
python scripts/journey_report.py
```

This prints the main customer journeys, detected intent, risk flags, handoff status and generated answer.

Example journeys:

```text
Normal high bill
High bill + vulnerability
Direct Debit change
Complaint
Gas leak emergency
Prompt injection
```

### Lex/Lambda-style fulfilment simulation

```bash
python scripts/simulate_lex_high_bill.py
```

This simulates:

```text
Lex-style event
  ↓
Lambda fulfilment handler
  ↓
ChatRequest
  ↓
Orchestration layer
  ↓
Lex-formatted response
  ↓
Connect-readable session attributes
```

The session attributes include values such as:

```text
orchestrator_intent
risk_flags
handoff_required
handoff_queue
connect_next_action
prompt_version
model_provider
```

---

## Test with curl

```bash
curl -s -X POST http://localhost:8001/chat \
  -H "Content-Type: application/json" \
  -d '{"channel":"chat","customer_id":"CUST001","message":"My bill is much higher than usual. Can you check why?"}' | python -m json.tool
```

Windows PowerShell alternative:

```powershell
$body = @{
  channel = "chat"
  customer_id = "CUST001"
  message = "My bill is much higher than usual. Can you check why?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/chat" -Method Post -ContentType "application/json" -Body $body
```

---

## Local mode

Local mode is the default.

In `.env`:

```env
MODEL_PROVIDER=local
PROMPT_VERSION=utility_assistant_v1
```

Local mode uses deterministic responses, which makes it suitable for:

- regression tests
- golden-case evaluations
- CI checks
- behaviour design
- safe local development

---

## Optional Bedrock mode

The project can optionally call an AWS Bedrock model through the Converse API.

Before enabling this mode:

1. Set an AWS billing alert.
2. Confirm your account has model access.
3. Confirm your account has non-zero invoke quota for the model.
4. Configure AWS credentials locally.
5. Update `.env`.

Example:

```env
MODEL_PROVIDER=bedrock
AWS_REGION=us-east-1
BEDROCK_MODEL_ID=<your-enabled-model-id>
```

Then restart the app.

Local mode should remain the default for tests and CI.

---

## Project structure

```text
app/
  main.py                  FastAPI entry point
  orchestrator.py          Main assistant workflow
  guardrails.py            Input and output safety checks
  rag.py                   Local retrieval
  tools.py                 Mocked business tools
  llm.py                   Local/Bedrock model provider switch
  schemas.py               Request/response schemas
  prompts/                 Versioned assistant instruction files
  knowledge_base/          Approved local knowledge articles

aws/
  lambda/
    lex_fulfilment_handler.py
  lex/
    lex_bot_design.md
  connect/
    contact_flow_design.md
  bedrock/
    bedrock_setup.md
    guardrails_design.md

evals/
  golden_cases.jsonl
  run_evals.py

scripts/
  journey_report.py
  simulate_lex_high_bill.py
  simulate_high_bill_ivr.py
  test_bedrock.py

tests/
  test_guardrails.py
  test_rag.py
  test_workflow.py
  test_vulnerability_handoff.py
  test_regulated_journeys.py
  test_lex_lambda_journeys.py

docs/
  00_TWO_DAY_CRASH_PLAN.md
  01_AWS_ARCHITECTURE.md
  02_AI_RESPONSE_DESIGN.md
  03_VOICE_IVR_DESIGN.md
  04_TOOL_CALLING_AND_AGENTIC_WORKFLOWS.md
  05_EVALUATION_AND_TESTING.md
  06_RELEASE_GOVERNANCE.md
  07_OBSERVABILITY_AND_CONTACT_CENTRE_METRICS.md
  08_UTILITIES_DOMAIN_GUIDE.md
  09_DAY_ONE_CHEAT_SHEET.md
  10_GLOSSARY.md
```

---

## Example safety report

```text
Journey:     Normal high bill
Intent:      billing_high
Risks:       none
Handoff:     False
Next action: answer_or_continue

Journey:     High bill + vulnerability
Intent:      billing_high
Risks:       vulnerability_or_hardship
Handoff:     True
Next action: handoff

Journey:     Direct Debit change
Intent:      direct_debit
Risks:       financial_or_high_impact_action
Handoff:     False
Next action: answer_or_continue

Journey:     Complaint
Intent:      complaint
Risks:       complaint_or_escalation
Handoff:     True
Next action: handoff
```

---

## Development commands

```bash
python -m pytest
python -m evals.run_evals
python scripts/journey_report.py
python scripts/simulate_lex_high_bill.py
```

Run the app:

```bash
uvicorn app.main:app --reload --port 8001
```

---

## Public-safety note

This repository uses fictional data, mocked tools and local knowledge articles.

It does not contain:

- real customer data
- real account data
- real supplier policy
- real payment instructions
- real emergency procedures
- production credentials
- production infrastructure configuration

Do not commit `.env`, AWS credentials, logs, account IDs or real customer information.

---

## License

MIT License.

