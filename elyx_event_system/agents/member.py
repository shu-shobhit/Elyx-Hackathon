# agents/member.py
import json
from typing import Dict, Any
from pprint import pprint
# LangChain components and your custom modules
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import MEMBER_PROFILE, INIT_MEMBER_SYSTEM, MEMBER_SYSTEM
from state import ConversationalState # Assuming state.py is in the parent directory
from utils import llm, append_message   # Assuming utils.py is in the parent directory

def init_member_node(state: ConversationalState) -> ConversationalState:
    """
    Initializes the member's state from the raw profile string.
    This node runs only once at the beginning of the graph execution.
    """
    print("--- Running Node: init_member_node ---")
    model = llm(temperature=0.4) # Low temperature for deterministic JSON output

    # The LLM's task is to convert the unstructured profile into a structured state
    content = model.invoke([
        SystemMessage(content=INIT_MEMBER_SYSTEM),
        HumanMessage(content=MEMBER_PROFILE)
    ]).content

    try:
        # The LLM should return a clean JSON string
        initial_member_state = json.loads(content)
        print(f"  -> Successfully parsed initial member state.")
    except json.JSONDecodeError:
        print(f"  -> ERROR: Failed to parse JSON from LLM output: {content}")
        # Fallback to a default state if parsing fails
        initial_member_state = {"error": "failed_to_initialize"}

    # Update the main ConversationalState
    state['member_state'] = initial_member_state
    state['chat_history'] = [] # Start with an empty chat history
    
    # Preserve week and thread tracking (these should already be set by main.py)
    if 'week_index' not in state:
        state['week_index'] = 1
    if 'thread_index' not in state:
        state['thread_index'] = 1
    if 'message_in_thread' not in state:
        state['message_in_thread'] = 0
    
    return state


def member_node(state: ConversationalState) -> ConversationalState:
    """
    Simulates the member's turn in the conversation. It can either
    initiate a new topic or respond to the Elyx team.
    """
    print("--- Running Node: member_node ---")
    model = llm(temperature=0.8)
    
    # --- NEW LOGIC to determine the task ---
    chat_history = state.get('chat_history', [])[-10:]
    new_thread_required = state.get('new_thread_required', False)

    if not chat_history:
        task = "initiate_onboarding"
        task_description = "This is your very first message to the Elyx team. Introduce yourself and state your primary health goals."
    elif new_thread_required:
        task = "initiate_new_conversation_thread"
        task_description = "The previous conversation has ended. Start a NEW conversation on a completely different topic. Base your new query on your persona and the simulation rules (e.g., upcoming travel, a question about your Garmin data, a new health trend you read about, or scheduling your next diagnostic test)."
        # CRITICAL: Reset the flag after using it.
        state['new_thread_required'] = False
    else:
        task = "respond"
        task_description = "You are in the middle of a conversation. Generate a realistic response to the last message from the Elyx team."

    # Build the context for the LLM
    context = {
        "task": task,
        # "task_description": task_description,
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-10:], # Provide last 5 messages for context
        "week_index": state.get("week_index", 1)
    }

    content = model.invoke([
        SystemMessage(content=MEMBER_SYSTEM),
        HumanMessage(content=json.dumps(context, indent=2))
    ]).content
    
    try:
        payload = json.loads(content)
        # Ensure the payload has the required keys
        message_text = payload.get("message", "Sorry, I'm not sure what to say.")
        decision = payload.get("decision", "END_TURN")
        is_travel_related = payload.get("is_travel_related", False)
        # print(f"  -> Member says: '{message_text}' (Decision: {decision})")
        if is_travel_related:
            if 'simulation_counters' in state['member_state']:
                state['member_state']['simulation_counters']['weeks_since_last_trip'] = 0
                print("  -> Travel topic detected. Resetting weeks_since_last_trip to 0.")
            else:
                print("  -> WARNING: is_travel_related was true but simulation_counters not found in state.")

    except Exception:
        print(f"  -> ERROR: Could not parse member_node JSON: {content}")
        message_text = content # Use the raw content as a fallback message
        decision = "END_TURN"

    # Update the shared state
    # This message is the new input for the router (RubyNode)
    state['message'] = message_text
    
    # Add the member's message to the history
    append_message(state, role="member", agent="member", text=message_text, meta={"decision": decision})
    
    # Print the response with timestamp
    # Get the timestamp from the last message in chat history
    chat_history = state.get("chat_history", [])
    if chat_history:
        timestamp = chat_history[-1].get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%a, %b %d, %I:%M %p")
                print(f"  [{time_str}] Member says: '{message_text}' (Decision: {decision})")
            except ValueError:
                print(f"  Member says: '{message_text}' (Decision: {decision})")
        else:
            print(f"  Member says: '{message_text}' (Decision: {decision})")
    else:
        print(f"  Member says: '{message_text}' (Decision: {decision})")
    
    # The 'decision' field can now be used by LangGraph's conditional routing
    # to decide whether to go to Ruby or to end the loop.
    # We will store it in the state for the router to access.
    state['member_decision'] = decision

    return state