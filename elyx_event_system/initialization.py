# initialization.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import MEMBER_PROFILE, INIT_MEMBER_SYSTEM
from state import ConversationalState
from utils import llm

def initialize_member_state() -> Dict[str, Any]:
    """
    Initialize the member's state from the raw profile string.
    This function runs only once during onboarding.
    
    Returns:
        Dict[str, Any]: The initial member state
    """
    print("=== Initializing Member State (Onboarding) ===")
    model = llm(temperature=0.4) # Low temperature for deterministic JSON output

    # The LLM's task is to convert the unstructured profile into a structured state
    content = model.invoke([
        SystemMessage(content=INIT_MEMBER_SYSTEM),
        HumanMessage(content=MEMBER_PROFILE)
    ]).content

    try:
        # The LLM should return a clean JSON string
        initial_member_state = json.loads(content)
        print(f"✅ Successfully parsed initial member state.")
        print(f"📋 Member profile keys: {list(initial_member_state.keys())}")
        return initial_member_state
    except json.JSONDecodeError:
        print(f"❌ ERROR: Failed to parse JSON from LLM output: {content}")
        # Fallback to a default state if parsing fails
        return {"error": "failed_to_initialize", "name": "Alex Tan", "goals": []}

def create_initial_conversational_state() -> ConversationalState:
    """
    Create the initial conversational state with member onboarding.
    This should be called only once at the start of the 35-week program.
    
    Returns:
        ConversationalState: The initial state ready for the first conversation
    """
    print("\n=== Creating Initial Conversational State ===")
    
    # Initialize member state through onboarding
    member_state = initialize_member_state()
    
    # Create the initial conversational state
    initial_state: ConversationalState = {
        "week_index": 1,
        "thread_index": 1,
        "message_in_thread": 0,
        "message": "",
        "chat_history": [],
        "member_state": member_state,
        "pending_agents": [],
        "current_agent": None,
        "member_decision": None,
        "active_events": [],
        "completed_events": [],
        "agent_responses": [],
        # Decision Tracking System fields
        "active_decision_chains": [],
        "completed_decision_chains": [],
        "current_decision_context": None
    }
    
    print("✅ Initial conversational state created successfully")
    print(f"👤 Member: {member_state.get('name', 'Unknown')}")
    print(f"🎯 Goals: {len(member_state.get('goals', []))} health goals identified")
    
    return initial_state
