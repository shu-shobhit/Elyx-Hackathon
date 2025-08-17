# orchestrator.py
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from pprint import pprint
from state import ConversationalState
from utils import llm, append_message, append_agent_response
from agents import AGENT_KEYS, AGENT_NODE_MAP, AGENT_FUNC_MAP
from agents.member import member_node
from prompts import DECISION_SYSTEM_PROMPT

# -------- Decider Function: Uses LLM to decide which node should come next ----------
def decide_next_node(state: ConversationalState) -> str:
    """
    Uses LLM to analyze the current conversation state and decide which agent
    should respond next, if the member should speak next, or if the conversation should end.
    """
    print("--- Running Node: Decider ---")
    
    # First, check for the member's explicit decision to end the turn.
    if state.get("member_decision") == "END_TURN":
        print("  -> Member ended their turn. Ending conversation loop.")
        return "END"  # Return "END" to match the conditional edges

    # --- CONTEXT DISTILLATION ---
    # Extract only the necessary information from the full state.
    chat_history = state.get("chat_history", [])
    agent_responses = state.get("agent_responses", [])
    member_state = state.get("member_state", {})

    # Determine the last speaker to enforce turn-taking.
    last_speaker_role = chat_history[-1]['role'] if chat_history else 'member'
    
    # Create a concise summary of the recent conversation.
    chat_summary = [
        f"{msg.get('agent') or msg.get('role', 'unknown')}: {msg.get('text', '')}"
        for msg in chat_history[-10:] # Last 5 messages are enough for context
    ]

    # Get the last agent's structured output, which is critical for handoffs.
    last_agent_structured_response = agent_responses[-1] if agent_responses else {}

    # Create a minimal summary of the member's profile for routing context.
    member_summary = {
        "name": member_state.get("name"),
        "goals": member_state.get("goals"),
        "risk_factors": member_state.get("risk_factors")
    }

    # Assemble the final, token-efficient context object.
    relevant_context = {
        "last_speaker_role": last_speaker_role,
        "member_message": state.get("message", ""),
        "chat_history_summary": chat_summary,
        "last_agent_structured_response": last_agent_structured_response,
        "member_summary": member_summary,
        "available_agents": AGENT_KEYS
    }
    human_prompt_content = json.dumps(relevant_context, indent=2)

    model = llm(temperature=0.4) 
    
    try:
        decision = model.invoke([
            SystemMessage(content=DECISION_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt_content)
        ]).content.strip().replace("\"", "")
        
        print(f"  -> Decider chose: {decision}")
        
        # Validate the decision
        if decision == "END":
            return "END"  # Return "END" to match the conditional edges
        elif decision == "Member":
            return "Member"
        elif decision in AGENT_KEYS:
            return AGENT_NODE_MAP[decision]
        else:
            print(f"  -> Invalid decision '{decision}', defaulting to Member.")
            return "Member"
            
    except Exception as e:
        print(f"  -> Error in decider: {e}, defaulting to Member.")
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
    # print("--- Running Node: agent_response_collector ---")
    
    # Get the last agent response for logging
    agent_responses = state.get("agent_responses", [])
    if agent_responses:
        last_response = agent_responses[-1]
        agent_name = last_response.get("agent", "Unknown")
        # print(f"  -> Processed {agent_name}'s response")
    
    return state


# -------- End Conversation Node ----------
def end_conversation_node(state: ConversationalState) -> ConversationalState:
    """
    Handles the end of the conversation turn.
    """
    print("--- Running Node: end_conversation_node ---")
    print("  -> Conversation turn ended")
    state['new_thread_required'] = True
    if 'simulation_counters' in state['member_state']:
        state['member_state']['simulation_counters']['weeks_since_last_trip'] += 1
    return state


def build_graph():
    g = StateGraph(ConversationalState)

    # Core nodes (removed InitMember)
    g.add_node("Member", member_node)
    g.add_node("Decider", decider_node)
    g.add_node("AgentResponseCollector", agent_response_collector)
    g.add_node("EndConversation", end_conversation_node)

    # Agent nodes
    for agent_key, func in AGENT_FUNC_MAP.items():
        g.add_node(AGENT_NODE_MAP[agent_key], func)

    # Main flow: Start → Member → Decider (removed InitMember)
    g.add_edge(START, "Member")
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
