# agents/advik.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import ADVIK_SYSTEM
from utils import llm, append_message, append_agent_response
from state import ConversationalState

def advik_node(state: ConversationalState) -> ConversationalState:
    model = llm(temperature=0.45)
    
    # Build context from shared state
    context = {
        "message": state.get("message", ""),
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-20:],
        "week_index": state.get("week_index", 0),
        "current_agent": state.get("current_agent", "Advik")
    }
    
    content = model.invoke([
        SystemMessage(content=ADVIK_SYSTEM),
        HumanMessage(content=json.dumps(context, indent=2))
    ]).content

    try:
        payload = json.loads(content)
        # Validate payload structure
        if "agent" not in payload:
            payload["agent"] = "Advik"
        if "message" not in payload:
            payload["message"] = content
        if "proposed_event" not in payload:
            payload["proposed_event"] = None
    except Exception:
        payload = {"agent": "Advik", "message": content, "proposed_event": None}

    # Update shared state
    append_agent_response(state, payload)
    append_message(state, role="advik", agent="Advik", text=payload.get("message", ""), 
                  meta={"source": "agent", "week_index": state.get("week_index", 0)})
    
    return state
