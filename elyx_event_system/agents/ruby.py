# agents/ruby.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import RUBY_SYSTEM
from utils import llm, append_message, append_agent_response
from state import ConversationalState
from pprint import pprint
def ruby_node(state: ConversationalState) -> ConversationalState:
    model = llm(temperature=0.6)
    
    # Build context from shared state
    context = {
        "message": state.get("message", ""),
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-10:],
        "week_index": state.get("week_index", 0),
        "current_agent": state.get("current_agent", "Ruby")
    }
    
    content = model.invoke([
        SystemMessage(content=RUBY_SYSTEM),
        HumanMessage(content=json.dumps(context, indent=2))
    ]).content

    try:
        payload = json.loads(content)
        # Validate payload structure
        if "agent" not in payload:
            payload["agent"] = "Ruby"
        if "message" not in payload:
            payload["message"] = content
        if "proposed_event" not in payload:
            payload["proposed_event"] = None
        if "needs_expert" not in payload:
            payload["needs_expert"] = "false"
        if "expert_needed" not in payload:
            payload["expert_needed"] = None
        if "routing_reason" not in payload:
            payload["routing_reason"] = ""
    except Exception:
        payload = {
            "agent": "Ruby", 
            "message": content, 
            "proposed_event": None,
            "needs_expert": "false",
            "expert_needed": None,
            "routing_reason": ""
        }

    # Update shared state
    append_agent_response(state, payload)
    append_message(state, role="ruby", agent="Ruby", text=payload.get("message", ""), 
                  meta={"source": "agent", "week_index": state.get("week_index", 0)})
    
    # Print the response with timestamp
    message_text = payload.get("message", "")
    # Get the timestamp from the last message in chat history
    chat_history = state.get("chat_history", [])
    if chat_history:
        timestamp = chat_history[-1].get("timestamp", "")
        if timestamp:
            try:
                from datetime import datetime
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%a, %b %d, %I:%M %p")
                print(f"  [{time_str}] Ruby says: '{message_text}'")
            except ValueError:
                print(f"  Ruby says: '{message_text}'")
        else:
            print(f"  Ruby says: '{message_text}'")
    else:
        print(f"  Ruby says: '{message_text}'")
    
    # Ensure we only store the message text, not the full JSON
    message_text = payload.get("message", "")
    if not message_text and isinstance(content, str):
        # If no message field, try to extract just the message from the content
        try:
            # Try to parse the content as JSON and extract just the message
            parsed_content = json.loads(content)
            message_text = parsed_content.get("message", "I apologize, but I couldn't generate a proper response.")
        except:
            # If parsing fails, use a generic message
            message_text = "I apologize, but I couldn't generate a proper response."
    
    state['message'] = message_text
    
    return state
