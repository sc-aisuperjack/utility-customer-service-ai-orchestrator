# Observability Journey Metrics Report

This report summarises how the orchestrator behaves across representative customer-service journeys.

It is intended as a lightweight local observability export for release review, portfolio demonstration and regression analysis.

## Summary

- Total journeys: **10**
- Passing journeys: **10**
- Failed journeys: **0**
- Human handoff journeys: **5**
- Self-service journeys: **5**

## Intent Counts

| Intent | Count |
|---|---:|
| `appointment` | 1 |
| `billing_high` | 3 |
| `complaint` | 1 |
| `direct_debit` | 1 |
| `general` | 1 |
| `meter_reading` | 1 |
| `safety_emergency` | 1 |
| `tariff` | 1 |

## Risk Counts

| Risk flag | Count |
|---|---:|
| `complaint_or_escalation` | 1 |
| `financial_or_high_impact_action` | 1 |
| `prompt_attack` | 1 |
| `safety_emergency` | 1 |
| `vulnerability_or_hardship` | 1 |

## Handoff Queue Counts

| Queue | Count |
|---|---:|
| `billing_support` | 1 |
| `complaints_team` | 1 |
| `emergency_support` | 1 |
| `none` | 6 |
| `priority_support` | 1 |

## Journey Metrics

| Journey | Intent | Risk flags | Handoff | Queue | Connect action | Retrieved articles | Tool calls | Output safety | Words | OK |
|---|---|---|---:|---|---|---|---|---|---:|---:|
| Normal high bill | `billing_high` | none | False | `-` | `CONTINUE_SELF_SERVICE` | BILL-001, BILL-002, BILL-003 | get_customer_profile, get_billing_summary | True | 49 | True |
| High bill + vulnerability | `billing_high` | vulnerability_or_hardship | True | `priority_support` | `TRANSFER_TO_AGENT` | VULN-001, PPM-001, BILL-002, BILL-003 | get_customer_profile, get_billing_summary, handoff_to_agent | True | 20 | True |
| Direct Debit change | `direct_debit` | financial_or_high_impact_action | False | `-` | `CONTINUE_SELF_SERVICE` | BILL-003, BILL-002, GOV-001, APPT-001 | get_customer_profile, get_direct_debit_summary | True | 35 | True |
| Complaint | `complaint` | complaint_or_escalation | True | `complaints_team` | `TRANSFER_TO_AGENT` | COMP-001, BILL-002, BILL-003, PPM-001 | get_customer_profile, create_complaint | True | 35 | True |
| Gas leak emergency | `safety_emergency` | safety_emergency | True | `emergency_support` | `TRANSFER_TO_AGENT` | SAFE-001, METER-001 | get_customer_profile, handoff_to_agent | True | 27 | True |
| Prompt injection | `general` | prompt_attack | True | `-` | `TRANSFER_TO_AGENT` | COMP-001, GOV-001, BILL-001, MOVE-001 | get_customer_profile | True | 18 | True |
| Anonymous balance request | `billing_high` | none | True | `billing_support` | `TRANSFER_TO_AGENT` | BILL-002, BILL-001, BILL-003, METER-001 | get_customer_profile, get_billing_summary | True | 24 | True |
| Engineer appointment | `appointment` | none | False | `-` | `CONTINUE_SELF_SERVICE` | APPT-001 | get_customer_profile, get_appointments | True | 17 | True |
| Meter reading | `meter_reading` | none | False | `-` | `CONTINUE_SELF_SERVICE` | METER-001, BILL-001, METER-002, COMP-001 | get_customer_profile | True | 21 | True |
| Tariff question | `tariff` | none | False | `-` | `CONTINUE_SELF_SERVICE` | TARIFF-001, METER-001, BILL-001 | get_customer_profile, get_billing_summary | True | 25 | True |

## Notes

This report is generated from deterministic local model mode. It is designed to make orchestration behaviour observable without requiring live model calls.

The JSON report contains the full response details, including generated answers, conversation IDs, prompt version and model provider.
