# agents/rachel.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import RACHEL_SYSTEM
from utils import llm, append_message, append_agent_response
from state import ConversationalState
from pprint import pprint
def rachel_node(state: ConversationalState) -> ConversationalState:
    model = llm(temperature=0.6)
    
    # Build context from shared state
    context = {
        "message": state.get("message", ""),
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-20:],
        "week_index": state.get("week_index", 0),
        "current_agent": state.get("current_agent", "Rachel")
    }
    
    content = model.invoke([
        SystemMessage(content=RACHEL_SYSTEM),
        HumanMessage(content=json.dumps(context, indent=2))
    ]).content

    try:
        payload = json.loads(content)
        # Validate payload structure
        if "agent" not in payload:
            payload["agent"] = "Rachel"
        if "message" not in payload:
            payload["message"] = content
        if "proposed_event" not in payload:
            payload["proposed_event"] = None
    except Exception:
        payload = {"agent": "Rachel", "message": content, "proposed_event": None}

    # Update shared state
    append_agent_response(state, payload)
    append_message(state, role="rachel", agent="Rachel", text=payload.get("message", ""), 
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
                print(f"  [{time_str}] Rachel says: '{message_text}'")
            except ValueError:
                print(f"  Rachel says: '{message_text}'")
        else:
            print(f"  Rachel says: '{message_text}'")
    else:
        print(f"  Rachel says: '{message_text}'")
    
    # Update the message field in state for the next iteration
    state['message'] = payload.get("message", content)
    
    return state
