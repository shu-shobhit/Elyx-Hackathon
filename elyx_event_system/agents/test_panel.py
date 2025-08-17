# agents/test_panel.py
import json
from typing import Dict, Any
from langchain_core.messages import SystemMessage, HumanMessage
from prompts import TEST_PANEL_SYSTEM
from utils import llm, append_message, append_agent_response
from state import ConversationalState
from pprint import pprint

def test_panel_node(state: ConversationalState) -> ConversationalState:
    """
    TestPanel agent that handles comprehensive diagnostic testing and generates
    realistic test results based on the member's conversation history.
    """
    model = llm(temperature=0.3)  # Low temperature for consistent medical results
    
    # Build context from shared state
    context = {
        "message": state.get("message", ""),
        "member_state": state.get("member_state", {}),
        "recent_chat": state.get("chat_history", [])[-20:],  
        "current_agent": state.get("current_agent", "TestPanel"),
        "active_events": state.get("active_events", [])
    }
    
    # Check if there are any diagnostic events to process
    diagnostic_events = [event for event in context["active_events"] 
                        if event.get("Type") == "Diagnostic" and event.get("status") == "proposed"]
    
    if diagnostic_events:
        # Process diagnostic testing
        content = model.invoke([
            SystemMessage(content=TEST_PANEL_SYSTEM),
            HumanMessage(content=json.dumps(context, indent=2))
        ]).content
    else:
        # No diagnostic events - provide general health assessment
        content = model.invoke([
            SystemMessage(content=TEST_PANEL_SYSTEM),
            HumanMessage(content=json.dumps(context, indent=2))
        ]).content

    try:
        payload = json.loads(content)
        # Validate payload structure
        if "agent" not in payload:
            payload["agent"] = "TestPanel"
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
        if "analysis" not in payload:
            payload["analysis"] = "Comprehensive health assessment completed"
        if "recommendations" not in payload:
            payload["recommendations"] = []
        if "medications" not in payload:
            payload["medications"] = []
        if "tests" not in payload:
            payload["tests"] = []
        if "confidence" not in payload:
            payload["confidence"] = 0.9
    except Exception:
        payload = {
            "agent": "TestPanel", 
            "message": content, 
            "proposed_event": None,
            "needs_expert": "false",
            "expert_needed": None,
            "routing_reason": "",
            "analysis": "Comprehensive health assessment completed",
            "recommendations": [],
            "medications": [],
            "tests": [],
            "confidence": 0.9
        }

    # Update shared state
    append_agent_response(state, payload)
    append_message(state, role="test_panel", agent="TestPanel", text=payload.get("message", ""), 
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
                print(f"  [{time_str}] TestPanel says: '{message_text}'")
            except ValueError:
                print(f"  TestPanel says: '{message_text}'")
        else:
            print(f"  TestPanel says: '{message_text}'")
    else:
        print(f"  TestPanel says: '{message_text}'")
    
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
