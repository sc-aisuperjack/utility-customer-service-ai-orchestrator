# Amazon Connect Contact Flow Design

```text
Start
  ↓
Play welcome prompt
  ↓
Get customer input
  ↓
Invoke Lex V2 bot
  ↓
Lex invokes Lambda fulfilment
  ↓
Lambda returns message and session attributes
  ↓
If handoff_required=true:
      Set contact attributes:
        intent
        risk_flags
        handoff_reason
        conversation_id
        prompt_version
      Transfer to queue
    Else:
      Play answer
      Ask if anything else
```

Preserve:
- conversation_id
- customer_id if authenticated
- intent
- risk_flags
- retrieved_article_ids
- handoff_reason
- prompt_version
- model_provider
- channel
