import json
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage

from state import ConversationalState
from utils import llm, append_message, append_agent_response
from agents import AGENT_KEYS, AGENT_NODE_MAP, AGENT_FUNC_MAP


# -------- Ruby First Response node: Ruby always responds first and decides routing ----------
def ruby_first_response_node(state: ConversationalState) -> ConversationalState:
    """
    Ruby is always the first point of contact. She responds to the member's query
    and decides if she needs to route to other experts.
    """
    # Set Ruby as the first agent
    state["pending_agents"] = ["Ruby"]
    state["current_agent"] = "Ruby"
    state["agent_responses"] = []
    return state

# -------- Conditional selector: where to go next ----------
def route_next(state: ConversationalState) -> str:
    pending = state.get("pending_agents", [])
    if not pending:
        return "Collector"
    
    # Get the next agent
    nxt = pending.pop(0)
    state["current_agent"] = nxt
    state["pending_agents"] = pending
    
    return AGENT_NODE_MAP[nxt]

# -------- Ruby Expert Routing node: handles Ruby's decision to route to experts ----------
def ruby_routing_node(state: ConversationalState) -> ConversationalState:
    """
    This node processes Ruby's response and determines if she needs to route to experts.
    Experts will respond directly to the member after Ruby routes to them.
    """
    # Get Ruby's last response
    agent_responses = state.get("agent_responses", [])
    ruby_response = None
    
    for response in agent_responses:
        if response.get("agent") == "Ruby":
            ruby_response = response
            break
    
    if ruby_response and ruby_response.get("needs_expert") == "true":
        expert_needed = ruby_response.get("expert_needed")
        if expert_needed and expert_needed in AGENT_KEYS:
            # Add the needed expert to the pending queue
            current_pending = state.get("pending_agents", [])
            if expert_needed not in current_pending:
                state["pending_agents"] = [expert_needed] + current_pending
                print(f"Ruby has routed to {expert_needed} for: {ruby_response.get('routing_reason', '')}")
    
    return state

# Ruby doesn't need to coordinate after experts - they respond directly to the member

# -------- Collector node ----------
def collector_node(state: ConversationalState) -> ConversationalState:
    return state

def build_graph():
    g = StateGraph(ConversationalState)

    # Nodes
    g.add_node("RubyFirst", ruby_first_response_node)
    g.add_node("RubyRouting", ruby_routing_node)
    g.add_node("Collector", collector_node)

    # Agent nodes
    for agent_key, func in AGENT_FUNC_MAP.items():
        g.add_node(AGENT_NODE_MAP[agent_key], func)

    # Flow: Start → RubyFirst → RubyNode → RubyRouting → route_next
    g.add_edge(START, "RubyFirst")
    g.add_edge("RubyFirst", "RubyNode")
    g.add_edge("RubyNode", "RubyRouting")
    
    # After RubyRouting, go to the conditional selector
    g.add_conditional_edges("RubyRouting", route_next, {
        "RubyNode": "RubyNode",
        "DrWarrenNode": "DrWarrenNode",
        "AdvikNode": "AdvikNode",
        "CarlaNode": "CarlaNode",
        "RachelNode": "RachelNode",
        "NeelNode": "NeelNode",
        "Collector": "Collector"
    })

    # After other agents, go to the conditional selector
    for node_name in AGENT_NODE_MAP.values():
        if node_name != "RubyNode":  # Skip Ruby since we handle it above
            g.add_conditional_edges(node_name, route_next, {
                "RubyNode": "RubyNode",
                "DrWarrenNode": "DrWarrenNode",
                "AdvikNode": "AdvikNode",
                "CarlaNode": "CarlaNode",
                "RachelNode": "RachelNode",
                "NeelNode": "NeelNode",
                "Collector": "Collector"
            })

    # When no more agents are pending, go directly to END
    g.add_edge("Collector", END)
    return g.compile()
