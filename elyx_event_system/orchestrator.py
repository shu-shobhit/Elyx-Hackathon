import json
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage

from state import ConversationalState
from prompts import ROUTER_SYSTEM, ROUTER_HUMAN_TEMPLATE
from utils import llm
from agents import AGENT_KEYS, AGENT_NODE_MAP, AGENT_FUNC_MAP


# -------- RouterInit node: selects agents and sets queue ----------
def router_init_node(state: ConversationalState) -> ConversationalState:
    model = llm(temperature=0.2)
    human = ROUTER_HUMAN_TEMPLATE.format(
        member_state=json.dumps(state.get("member_state", {}), indent=2),
        chat_history=json.dumps(state.get("chat_history", [])[-20:], indent=2),
        message=state.get("message", "")
    )
    out = model.invoke([
        SystemMessage(content=ROUTER_SYSTEM),
        HumanMessage(content=human)
    ]).content

    try:
        chosen = json.loads(out)
        chosen = [c for c in chosen if c in AGENT_KEYS]
    except Exception:
        chosen = []

    state["pending_agents"] = chosen
    state["current_agent"] = None
    state["agent_responses"] = []
    return state

# -------- Conditional selector: where to go next ----------
def route_next(state: ConversationalState) -> str:
    pending = state.get("pending_agents", [])
    if not pending:
        return "Collector"
    nxt = pending.pop(0)
    state["current_agent"] = nxt
    state["pending_agents"] = pending
    return AGENT_NODE_MAP[nxt]

# -------- Collector node ----------
def collector_node(state: ConversationalState) -> ConversationalState:
    return state

def build_graph():
    g = StateGraph(ConversationalState)

    # Nodes
    g.add_node("RouterInit", router_init_node)
    g.add_node("Collector", collector_node)

    # Agent nodes
    for agent_key, func in AGENT_FUNC_MAP.items():
        g.add_node(AGENT_NODE_MAP[agent_key], func)

    # Flow
    g.add_edge(START, "RouterInit")
    g.add_conditional_edges("RouterInit", route_next, {
        "RubyNode": "RubyNode",
        "DrWarrenNode": "DrWarrenNode",
        "AdvikNode": "AdvikNode",
        "CarlaNode": "CarlaNode",
        "RachelNode": "RachelNode",
        "NeelNode": "NeelNode",
        "Collector": "Collector"
    })

    # After each agent, go to the conditional selector (NOT back to RouterInit)
    for node_name in AGENT_NODE_MAP.values():
        g.add_conditional_edges(node_name, route_next, {
            "RubyNode": "RubyNode",
            "DrWarrenNode": "DrWarrenNode",
            "AdvikNode": "AdvikNode",
            "CarlaNode": "CarlaNode",
            "RachelNode": "RachelNode",
            "NeelNode": "NeelNode",
            "Collector": "Collector"
        })

    g.add_edge("Collector", END)
    return g.compile()
