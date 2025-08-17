# agents/ruby.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import RUBY_SYSTEM
from utils import llm, append_message, append_agent_response
from state import ConversationalState
from pprint import pprint
def ruby_node(state: ConversationalState) -> ConversationalState:
    model = llm(temperature=0.5)
    
    # Build context from shared state
    context = {
        "message": state.get("message", ""),
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-20:],
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
    
    # Print the response
    print(f"  -> Ruby says: '{payload.get('message', '')}'")
    
    state['message'] = payload.get("message", content)
    
    return state
