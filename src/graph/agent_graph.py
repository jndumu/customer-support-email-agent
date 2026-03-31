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
  send_node          — Promotes draft → final_response              escalate_node
     │                  Sends via SMTP (if configured)               — Generates holding
     │                  Schedules follow-up if flagged                 message for customer
     ▼                                                               — Alerts human team
  [END]                                                                      │
                                                                             ▼
                                                                           [END]
─────────────────────────────────────────────────────────────────────────────

CONDITIONAL ROUTING:
  route_after_classify:
    escalate=True  → escalate_node
    escalate=False → retrieve_node

  route_after_review:
    passed=True AND needs_human_review=False → send_node
    anything else                           → escalate_node
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
# These are pure functions — they inspect state and return a node name string.
# LangGraph uses the returned value to resolve the next node from the
# edges dict passed to add_conditional_edges().

def route_after_classify(state: AgentState) -> str:
    """Route immediately to escalation for legal/safety/urgent cases;
    otherwise proceed to knowledge retrieval."""
    if state.get("escalate"):
        return "escalate"
    return "retrieve"


def route_after_review(state: AgentState) -> str:
    """Route to send if the draft passed QA and no human sign-off is needed;
    escalate otherwise to ensure unsafe drafts never reach the customer."""
    if state.get("needs_human_review") or not state.get("review_passed"):
        return "escalate"
    return "send"


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """Construct and return the compiled LangGraph StateGraph.

    Nodes are registered first, then edges are added to define the execution
    order. Conditional edges allow dynamic branching based on runtime state.
    """
    graph = StateGraph(AgentState)

    # ── Register nodes ────────────────────────────────────────────────────
    # Each node is a plain Python function: (AgentState) → AgentState
    graph.add_node("ingest", ingest_node)
    graph.add_node("classify", classify_node)
    graph.add_node("retrieve", retrieve_node)
    graph.add_node("draft", draft_node)
    graph.add_node("review", review_node)
    graph.add_node("escalate", escalate_node)
    graph.add_node("send", send_node)

    # ── Entry point ───────────────────────────────────────────────────────
    graph.set_entry_point("ingest")

    # ── Fixed (unconditional) edges ───────────────────────────────────────
    graph.add_edge("ingest", "classify")       # always classify after ingest
    graph.add_edge("retrieve", "draft")        # always draft after retrieval
    graph.add_edge("draft", "review")          # always review the draft
    graph.add_edge("escalate", END)            # escalation is always terminal
    graph.add_edge("send", END)                # send is always terminal

    # ── Conditional edges ─────────────────────────────────────────────────
    # classify → (escalate | retrieve)
    graph.add_conditional_edges(
        "classify",
        route_after_classify,
        {
            "escalate": "escalate",
            "retrieve": "retrieve",
        },
    )
    # review → (send | escalate)
    graph.add_conditional_edges(
        "review",
        route_after_review,
        {
            "send": "send",
            "escalate": "escalate",
        },
    )

    return graph


# ── Compiled graph ────────────────────────────────────────────────────────────
# Import this singleton in the API layer:
#   from src.graph.agent_graph import agent_graph
#   result = await agent_graph.ainvoke(initial_state)
agent_graph = build_graph().compile()
