from app.orchestrator import handle_chat
from app.schemas import ChatRequest

print("Local Utility Assistant CLI. Type 'quit' to exit.")
customer_id = input("Customer ID [CUST001/CUST002/ANON]: ").strip() or "CUST001"
channel = input("Channel [chat/voice/sms/whatsapp]: ").strip() or "chat"

while True:
    msg = input("\nCustomer: ").strip()
    if msg.lower() in {"quit", "exit"}:
        break
    response = handle_chat(ChatRequest(customer_id=customer_id, channel=channel, message=msg))
    print("\nAssistant:", response.answer_for_customer)
    print("Intent:", response.decision.intent)
    print("Risks:", response.decision.risk_flags)
    print("Handoff:", response.decision.requires_handoff, response.decision.handoff_reason)
