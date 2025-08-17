# orchestrator.py
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from pprint import pprint
from state import ConversationalState
from utils import llm, append_message, append_agent_response
from agents import AGENT_KEYS, AGENT_NODE_MAP, AGENT_FUNC_MAP
from agents.member import init_member_node, member_node
from prompts import DECISION_SYSTEM_PROMPT

# -------- Decider Function: Uses LLM to decide which node should come next ----------
def decide_next_node(state: ConversationalState) -> str:
    """
    Uses LLM to analyze the current conversation state and decide which agent
    should respond next, if the member should speak next, or if the conversation should end.
    """
    print("--- Running Node: decider_node ---")
    
    # Get the current conversation context
    chat_history = state.get("chat_history", [])
    member_state = state.get("member_state", {})
    current_message = state.get("message", "")
    member_decision = state.get("member_decision", "CONTINUE_CONVERSATION")
    agent_responses = state.get("agent_responses", {})
    # Check if member wants to end the conversation
    if member_decision == "END_TURN":
        print(f"  -> Member decided to end turn, ending conversation")
        return "END"
    
    # # Build context for the LLM
    # context = {
    #     "current_message": current_message,
    #     "recent_chat": chat_history[-10:-1] if chat_history else [], # Last 10 messages
    #     "recent_agent_responses" : agent_responses[-5:],
    #     "member_state": member_state,
    # }

    context = f"""Here is the current conversational state. Analyze it according to your instructions and provide your single-word decision.
CURRENT_STATE:
{json.dumps(state, indent=2, default=str)}
"""
    model = llm(temperature=0.2)  # Low temperature for consistent decisions
    
    try:
        decision = model.invoke([
            SystemMessage(content=DECISION_SYSTEM_PROMPT),
            HumanMessage(content=context)
        ]).content.strip()
        
        print(f"  -> Decider chose: {decision}")
        
        # Validate the decision
        if decision == "END":
            return "END"
        elif decision == "Member":
            return "Member"
        elif decision in AGENT_KEYS:
            return AGENT_NODE_MAP[decision]
        else:
            print(f"  -> Invalid decision '{decision}', defaulting to Member")
            return "Member"
            
    except Exception as e:
        print(f"  -> Error in decider: {e}, defaulting to Member")
        return "Member"


# -------- Decider Node: Just passes through the state ----------
def decider_node(state: ConversationalState) -> ConversationalState:
    """
    This node just passes through the state. The actual decision logic
    is handled by the conditional edge function.
    """
    return {}


# -------- Agent Response Collector Node ----------
def agent_response_collector(state: ConversationalState) -> ConversationalState:
    """
    Collects and processes the agent's response. The agent has already added
    their response to chat history, so this node just passes through the state.
    """
    print("--- Running Node: agent_response_collector ---")
    
    # Get the last agent response for logging
    agent_responses = state.get("agent_responses", [])
    if agent_responses:
        last_response = agent_responses[-1]
        agent_name = last_response.get("agent", "Unknown")
        print(f"  -> Processed {agent_name}'s response")
    
    return state


# -------- End Conversation Node ----------
def end_conversation_node(state: ConversationalState) -> ConversationalState:
    """
    Handles the end of the conversation turn.
    """
    print("--- Running Node: end_conversation_node ---")
    print("  -> Conversation turn ended")
    return state


def build_graph():
    g = StateGraph(ConversationalState)

    # Core nodes
    g.add_node("InitMember", init_member_node)
    g.add_node("Member", member_node)
    g.add_node("Decider", decider_node)
    g.add_node("AgentResponseCollector", agent_response_collector)
    g.add_node("EndConversation", end_conversation_node)

    # Agent nodes
    for agent_key, func in AGENT_FUNC_MAP.items():
        g.add_node(AGENT_NODE_MAP[agent_key], func)

    # Main flow: Start → InitMember → Member → Decider
    g.add_edge(START, "InitMember")
    g.add_edge("InitMember", "Member")
    g.add_edge("Member", "Decider")
    
    # Decider routes to agents, member, or ends conversation
    decider_edges = {
        "END": "EndConversation",
        "Member": "Member"
    }
    
    # Add edges for all agents
    for node_name in AGENT_NODE_MAP.values():
        decider_edges[node_name] = node_name
    
    g.add_conditional_edges("Decider", decide_next_node, decider_edges)
    
    # After each agent responds, collect the response and go back to decider
    for node_name in AGENT_NODE_MAP.values():
        g.add_edge(node_name, "AgentResponseCollector")
    
    # After collecting agent response, go back to decider
    g.add_edge("AgentResponseCollector", "Decider")
    
    # End the conversation
    g.add_edge("EndConversation", END)
    
    return g.compile()
