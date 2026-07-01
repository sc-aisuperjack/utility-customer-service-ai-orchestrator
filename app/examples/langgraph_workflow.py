"""
Optional LangGraph exercise.

Install:
  pip install -r requirements-optional.txt

Run:
  python -m app.examples.langgraph_workflow
"""
from typing import TypedDict, List, Any
from langgraph.graph import StateGraph, START, END
from app.guardrails import apply_input_guardrails
from app.rag import retrieve
from app.orchestrator import classify_intent, run_tools
from app.llm import local_model_response

class State(TypedDict, total=False):
    customer_id: str
    channel: str
    message: str
    redacted: str
    risks: List[str]
    intent: str
    docs: List[Any]
    tool_results: List[Any]
    answer: str

def guard_node(state: State) -> State:
    g = apply_input_guardrails(state["message"])
    return {"redacted": g.redacted, "risks": g.risks}

def intent_node(state: State) -> State:
    return {"intent": classify_intent(state["redacted"], state["risks"])}

def retrieve_node(state: State) -> State:
    return {"docs": retrieve(state["redacted"])}

def tools_node(state: State) -> State:
    return {"tool_results": run_tools(state["intent"], state["customer_id"], state["risks"], state["redacted"])}

def answer_node(state: State) -> State:
    return {"answer": local_model_response(state["channel"], state["redacted"], state["intent"], state["risks"], state["docs"], state["tool_results"])}

def build_graph():
    graph = StateGraph(State)
    graph.add_node("guard", guard_node)
    graph.add_node("classify_intent", intent_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("tools", tools_node)
    graph.add_node("answer", answer_node)
    graph.add_edge(START, "guard")
    graph.add_edge("guard", "classify_intent")
    graph.add_edge("classify_intent", "retrieve")
    graph.add_edge("retrieve", "tools")
    graph.add_edge("tools", "answer")
    graph.add_edge("answer", END)
    return graph.compile()

if __name__ == "__main__":
    app = build_graph()
    out = app.invoke({"customer_id": "CUST001", "channel": "chat", "message": "My bill is much higher than usual. Can you check why?"})
    print(out["answer"])
