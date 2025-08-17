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
    
    # Build context for the LLM
    context = {
        "current_message": current_message,
        "recent_chat": chat_history[-10:-1] if chat_history else [], # Last 10 messages
        "recent_agent_responses" : agent_responses[-5:],
        "member_state": member_state,
    }
    
    
    # Create the decision prompt
    decision_prompt = f"""
You are the conversation flow controller for Elyx, a preventative healthcare service.

**Current Context:**
- Member's latest message: "{current_message}"
- Recent conversation: {json.dumps([msg.get('text', '') for msg in context['recent_chat']], indent=2)}
- Member state: {json.dumps(member_state, indent=2)}

**Available Options:**
- Ruby: Concierge/Primary contact (general coordination, logistics)
- DrWarren: Medical strategist (labs, diagnostics, clinical decisions)
- Advik: Performance scientist (wearable data, sleep, HRV analysis)
- Carla: Nutritionist (diet, CGM, supplements)
- Rachel: Physiotherapist (exercise, mobility, rehab)
- Neel: Strategic lead (QBRs, long-term planning)
- Member: Let the member speak next (they should respond to the last agent)
- END: End the conversation

**Decision Rules:**
1. **CRITICAL**: If the last message in the conversation is from an agent, then choose next among other options.
2. If the last message is from the member and requires a response, choose the most appropriate agent.
3. If the conversation feels complete and the member feels satisfied, return "END".
4. Ruby should handle general questions and coordination.
5. Specialized questions should go to the appropriate expert.
6. **IMPORTANT**: After ANY agent responds, typically the member should have a chance to reply before another agent speaks.

**Output Format:**
Return ONLY the agent name (e.g., "Ruby", "DrWarren"), "Member", or "END".
"""

    model = llm(temperature=0.1)  # Low temperature for consistent decisions
    
    try:
        decision = model.invoke([
            SystemMessage(content="You are a conversation flow controller. Respond with only the agent name, 'Member', or 'END'."),
            HumanMessage(content=decision_prompt)
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
