# Amazon Lex V2 Bot Design

Bot name: `UtilityCustomerServiceBot`

## Intents

### HighBillIntent
Utterances:
- My bill is too high
- Why is my bill higher than usual
- I don't understand my charges

### MeterReadingIntent
Utterances:
- I want to submit a meter reading
- My reading is 12345

### ComplaintIntent
Utterances:
- I want to complain
- I want to escalate this
- I am going to the Ombudsman

### VulnerabilitySupportIntent
Utterances:
- I use medical equipment
- I cannot afford to top up
- I need extra support

### SafetyEmergencyIntent
Utterances:
- I smell gas
- Carbon monoxide alarm is going off
- I see sparks

Fulfilment:
Lex -> Lambda -> guardrails -> RAG -> tools -> Bedrock/local -> Lex response.
