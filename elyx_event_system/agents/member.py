# agents/member.py
import json
from typing import Dict, Any
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
    state['week_index'] = 1    # Start at week 1
    
    return state


def member_node(state: ConversationalState) -> ConversationalState:
    """
    Simulates the member's turn in the conversation. It can either
    initiate a new topic or respond to the Elyx team.
    """
    print("--- Running Node: member_node ---")
    model = llm(temperature=0.8) # Higher temperature for creative, human-like messages
    
    # Determine the task: Is this the first message or a reply?
    if not state.get('chat_history'):
        task = "initiate"
        task_description = "You are starting your journey with Elyx. Generate your first message to your concierge, Ruby. It could be a simple greeting or a question about getting started."
    else:
        task = "respond"
        task_description = "The Elyx team has just sent you one or more messages. Based on your current state and the last few messages, generate a realistic response. Decide if you are expecting another reply or if this turn of the conversation is over."

    # Build the context for the LLM
    context = {
        "task": task,
        "task_description": task_description,
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-5:], # Provide last 5 messages for context
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
        print(f"  -> Member says: '{message_text}' (Decision: {decision})")

    except Exception:
        print(f"  -> ERROR: Could not parse member_node JSON: {content}")
        message_text = content # Use the raw content as a fallback message
        decision = "END_TURN"

    # Update the shared state
    # This message is the new input for the router (RubyNode)
    state['message'] = message_text
    
    # Add the member's message to the history
    append_message(state, role="member", text=message_text, meta={"decision": decision})
    
    # The 'decision' field can now be used by LangGraph's conditional routing
    # to decide whether to go to Ruby or to end the loop.
    # We will store it in the state for the router to access.
    state['member_decision'] = decision

    return state