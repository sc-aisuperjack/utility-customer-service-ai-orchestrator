from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from app.schemas import ChatRequest, ChatResponse
from app.orchestrator import handle_chat
from app.prompt_loader import list_prompts
from app.tools import available_tools_manifest
from app.rag import load_docs

app = FastAPI(title="Utility Customer Service AI Orchestrator", version="1.0.0")

@app.get("/health")
def health():
    return {"ok": True}

@app.get("/prompts")
def prompts():
    return {"prompts": list_prompts()}

@app.get("/tools")
def tools():
    return {"tools": available_tools_manifest()}

@app.get("/knowledge")
def knowledge():
    return {"count": len(load_docs()), "docs": load_docs()}

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    return handle_chat(req)

HTML = """
<!doctype html>
<html>
<head>
  <title>Utility Customer Service AI Orchestrator</title>
  <style>
    body { font-family: Arial, sans-serif; max-width: 960px; margin: 40px auto; line-height: 1.5; }
    textarea { width: 100%; height: 120px; }
    select, input, button { padding: 8px; margin: 4px 0; }
    pre { background: #f4f4f4; padding: 16px; overflow: auto; }
    .row { display: flex; gap: 12px; }
    .row > div { flex: 1; }
  </style>
</head>
<body>
<h1>Utility Customer Service AI Orchestrator</h1>
<p>Local-first utility customer-service assistant for AWS with prompts, RAG, tools, guardrails and evals.</p>

<div class="row">
  <div>
    <label>Customer</label><br>
    <select id="customer_id">
      <option value="CUST001">CUST001 - normal billing example</option>
      <option value="CUST002">CUST002 - PSR/vulnerability example</option>
      <option value="ANON">ANON - unauthenticated</option>
    </select>
  </div>
  <div>
    <label>Channel</label><br>
    <select id="channel">
      <option value="chat">chat</option>
      <option value="voice">voice</option>
      <option value="sms">sms</option>
      <option value="whatsapp">whatsapp</option>
    </select>
  </div>
</div>

<label>Message</label>
<textarea id="message">My bill is much higher than usual. Can you check why?</textarea>
<br>
<button onclick="send()">Send</button>

<h2>Response</h2>
<pre id="out">Waiting...</pre>

<script>
async function send() {
  const payload = {
    customer_id: document.getElementById("customer_id").value,
    channel: document.getElementById("channel").value,
    message: document.getElementById("message").value
  };
  const res = await fetch("/chat", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify(payload)
  });
  const data = await res.json();
  document.getElementById("out").textContent = JSON.stringify(data, null, 2);
}
</script>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
def home():
    return HTML
