# orchestrator.py
import json
from typing import Dict, Any
from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage
from pprint import pprint
from state import ConversationalState
from utils import llm, append_message, append_agent_response, create_decision_chain, add_agent_analysis, finalize_decision
from agents import AGENT_KEYS, AGENT_NODE_MAP, AGENT_FUNC_MAP
from agents.member import member_node
from prompts import DECISION_SYSTEM_PROMPT

# -------- Diagnostic Scheduling Function ----------
def should_schedule_diagnostic(state: ConversationalState) -> bool:
    """
    Checks if it's time to schedule a diagnostic test panel (every 12 weeks).
    """
    if 'simulation_counters' not in state.get('member_state', {}):
        return False
    
    counters = state['member_state']['simulation_counters']
    weeks_since_diagnostic = counters.get('weeks_since_last_diagnostic', 0)
    
    # Schedule diagnostics every 12 weeks
    return weeks_since_diagnostic >= 12

def create_diagnostic_event(state: ConversationalState) -> str:
    """
    Creates a comprehensive diagnostic event when diagnostics are due.
    """
    from utils import create_event
    
    # Create the diagnostic event
    event_id = create_event(
        state, 
        event_type="Diagnostic", 
        description="Comprehensive Health Assessment - 12-week diagnostic panel including blood tests, cardiovascular assessment, body composition, and specialized screenings",
        reason="Scheduled diagnostic testing due every 12 weeks",
        priority="High",
        created_by="System"
    )
    
    # Reset the diagnostic counter
    if 'simulation_counters' in state.get('member_state', {}):
        state['member_state']['simulation_counters']['weeks_since_last_diagnostic'] = 0
    
    print(f"  -> Created diagnostic event: {event_id}")
    return event_id

# -------- Quarterly Test Panel Check Function ----------
def should_run_test_panel(state: ConversationalState) -> bool:
    """
    Checks if it's time to run the quarterly test panel (every 12 weeks).
    """
    week_index = state.get("week_index", 0)
    last_test_panel = state.get("last_test_panel", None)
    
    # If no test panel has been run yet, run it at week 0
    if last_test_panel is None:
        return True
    
    # Check if 12 weeks (3 months) have passed since last test panel
    last_test_week = last_test_panel.get("week_index", 0)
    weeks_since_last_test = week_index - last_test_week
    
    return weeks_since_last_test >= 12

# -------- Decision Point Detection Function ----------
def detect_decision_point(state: ConversationalState) -> bool:
    """
    Detects if the current conversation state indicates a decision point.
    Only returns True for actual decisions, not routine responses.
    """
    agent_responses = state.get("agent_responses", [])
    if not agent_responses:
        return False
    
    last_response = agent_responses[-1]
    
    # Check for actual decision indicators
    has_recommendations = bool(last_response.get("recommendations"))
    has_medications = bool(last_response.get("medications"))
    has_tests = bool(last_response.get("tests"))
    has_analysis = bool(last_response.get("analysis"))
    has_confidence = last_response.get("confidence", 0) > 0.5
    
    # Must have at least 2 significant decision indicators
    decision_indicators = sum([
        has_recommendations,
        has_medications, 
        has_tests,
        has_analysis and has_confidence  # Analysis must also have confidence
    ])
    
    # Only consider it a decision if there are multiple indicators
    return decision_indicators >= 2

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

    # --- DIAGNOSTIC SCHEDULING CHECK ---
    # Check if diagnostics are due and schedule them automatically
    if should_schedule_diagnostic(state):
        print("  -> Diagnostics due - scheduling comprehensive health assessment")
        create_diagnostic_event(state)
        # Route to TestPanel to conduct the diagnostic testing
        return "TestPanelNode"

    # --- DECISION TRACKING INTEGRATION ---
    # Check if we need to create or update a decision chain
    if detect_decision_point(state):
        agent_responses = state.get("agent_responses", [])
        if agent_responses:
            last_response = agent_responses[-1]
            agent_name = last_response.get("agent", "Unknown")
            
            # Check if we already have an active decision chain
            active_chains = state.get("active_decision_chains", [])
            if not active_chains:
                # Create a new decision chain only for significant decisions
                member_id = state.get("member_state", {}).get("name", "Unknown")
                triggering_event = f"{agent_name} made recommendations/decisions"
                decision_id = create_decision_chain(state, triggering_event, member_id)
                print(f"  -> Created new decision chain: {decision_id}")
            
            # Add the agent's analysis to the current decision chain
            if active_chains:
                current_chain = active_chains[0]  # Get the most recent active chain
                
                # Check if this agent's analysis has already been added to this decision chain
                existing_analyses = current_chain.get("agent_analyses", [])
                agent_already_added = any(
                    analysis.get("agent_name") == agent_name 
                    for analysis in existing_analyses
                )
                
                # Only add if this agent hasn't been added to this decision chain yet
                if not agent_already_added:
                    # Determine analysis type based on agent
                    analysis_type = "general_analysis"
                    if agent_name == "DrWarren":
                        analysis_type = "clinical_analysis"
                    elif agent_name == "Carla":
                        analysis_type = "nutritional_analysis"
                    elif agent_name == "Rachel":
                        analysis_type = "exercise_analysis"
                    elif agent_name == "Advik":
                        analysis_type = "data_analysis"
                    
                    add_agent_analysis(
                        state, 
                        current_chain["decision_id"],
                        agent_name,
                        analysis_type,
                        [last_response.get("analysis", "")] if last_response.get("analysis") else [],
                        last_response.get("confidence", 0.7),
                        last_response.get("recommendations", []),
                        last_response.get("medications", []) + last_response.get("tests", [])
                    )
                    print(f"  -> Added {agent_name}'s analysis to decision chain")
                else:
                    print(f"  -> {agent_name}'s analysis already added to current decision chain")

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
            # Finalize any active decision chains before ending
            active_chains = state.get("active_decision_chains", [])
            if active_chains:
                for chain in active_chains:
                    finalize_decision(state, chain["decision_id"], "Conversation ended", "Conversation ended")
                print("  -> Finalized active decision chains")
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
        state['member_state']['simulation_counters']['weeks_since_last_diagnostic'] += 1
    
    # Finalize any active decision chains
    active_chains = state.get("active_decision_chains", [])
    if active_chains:
        for chain in active_chains:
            finalize_decision(
                state, 
                chain["decision_id"], 
                "Conversation thread ended", 
                "Decision chain completed with conversation",
                "System"
            )
        print(f"  -> Finalized {len(active_chains)} active decision chains")
    
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
    # EXCEPT for TestPanel - it goes directly back to Decider
    for node_name in AGENT_NODE_MAP.values():
        if node_name != "TestPanelNode":  # Skip TestPanel for normal flow
            g.add_edge(node_name, "AgentResponseCollector")
    
    # TestPanel goes directly back to Decider (bypassing AgentResponseCollector)
    g.add_edge("TestPanelNode", "Decider")
    
    # After collecting agent response, go back to decider
    g.add_edge("AgentResponseCollector", "Decider")
    
    # End the conversation
    g.add_edge("EndConversation", END)
    
    return g.compile()
