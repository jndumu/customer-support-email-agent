"""LangGraph workflow — wires all nodes into the customer support email pipeline.

FULL PIPELINE FLOW:
─────────────────────────────────────────────────────────────────────────────
  [START]
     │
     ▼
  ingest_node        — Cleans the email body (strips signatures, quoted replies)
     │
     ▼
  classify_node      — LLM classifies intent, priority, sentiment, and decides
     │                  whether to escalate immediately (legal/safety/urgency)
     │
     ├── escalate=True ──────────────────────────────────────────────────────┐
     │                                                                       │
     ▼                                                                       │
  retrieve_node      — Searches knowledge base (Pinecone or local BM25)      │
     │                  for the most relevant FAQ / policy chunks             │
     ▼                                                                       │
  draft_node         — LLM generates a grounded, tone-appropriate reply       │
     │                  using retrieved docs + intent/sentiment context       │
     ▼                                                                       │
  review_node        — LLM reviews draft for accuracy, tone, policy          │
     │                  compliance, and decides if human sign-off is needed   │
     │                                                                       │
     ├── needs_human_review=True OR review_passed=False ────────────────────┤
     │                                                                       │
     ▼                                                                       ▼
  send_node          — Promotes draft → final_response           escalation_node
     │                  Sends via SMTP (if configured)             — Generates holding
     │                  Schedules follow-up if flagged               message for customer
     ▼                                                             — Alerts human team
  [END]                                                                      │
                                                                             ▼
                                                                           [END]
─────────────────────────────────────────────────────────────────────────────

CONDITIONAL ROUTING:
  route_after_classify:
    escalate=True  → escalation_node
    escalate=False → retrieve_node

  route_after_review:
    passed=True AND needs_human_review=False → send_node
    anything else                           → escalation_node

NOTE: The node is named "escalation" (not "escalate") because LangGraph 0.5+
rejects node names that collide with AgentState field names, and our state
has `escalate: bool`.
"""

from langgraph.graph import StateGraph, END

from src.graph.state import AgentState
from src.nodes.ingest import ingest_node
from src.nodes.classify import classify_node
from src.nodes.retrieve import retrieve_node
from src.nodes.draft import draft_node
from src.nodes.review import review_node
from src.nodes.escalate import escalate_node
from src.nodes.send import send_node


# ── Routing functions ─────────────────────────────────────────────────────────

def route_after_classify(state: AgentState) -> str:
    """Route immediately to escalation for legal/safety/urgent cases;
    otherwise proceed to knowledge retrieval."""
    if state.get("escalate"):
        return "escalation"
    return "retrieve"


def route_after_review(state: AgentState) -> str:
    """Route to send if the draft passed QA and no human sign-off is needed;
    escalate otherwise to ensure unsafe drafts never reach the customer."""
    if state.get("needs_human_review") or not state.get("review_passed"):
        return "escalation"
    return "send"


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    graph = StateGraph(AgentState)

    graph.add_node("ingest", ingest_node)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("escalation", escalate_node)   # "escalation" avoids clash with state key "escalate"
    graph.add_node("send", send_node)

    graph.set_entry_point("ingest")

    graph.add_edge("ingest", "classify")
    graph.add_edge("retrieve", "draft")
    graph.add_edge("draft", "review")
    graph.add_edge("escalation", END)
    graph.add_edge("send", END)

    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {"escalation": "escalation", "retrieve": "retrieve"},
    )
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {"send": "send", "escalation": "escalation"},
    )

    return graph


agent_graph = build_graph().compile()
