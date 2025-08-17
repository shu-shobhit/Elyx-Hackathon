# state.py
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator
from pprint import pprint
from datetime import datetime

class ChatMsg(TypedDict):
    role: str       # "member" | "ruby" | "dr_warren" | ...
    agent: Optional[str]   # Agent key when role is an Elyx team member
    text: str       # WhatsApp-style message text
    msg_id: str
    timestamp: str  # When the message was sent (ISO format string)
    event_id: Optional[str]  # ID of the event this message relates to
    meta: Optional[Dict[str, Any]]

class EventObj(TypedDict):
    event_id: str
    Type: str
    description: str
    reason: str
    priority: str    # "High" | "Medium" | "Low"
    status: str      # "proposed" | "scheduled" | "confirmed" | "completed" | "cancelled"
    created_by: str  # Agent who created the event
    created_at: str  # Timestamp when event was created
    meta: Dict[str, Any]

class AgentOutput(TypedDict, total=False):
    agent: str 
    message: str
    proposed_event: Optional[EventObj]
    event_id: Optional[str]  # ID of the event being referenced/created
    needs_expert: Optional[str]  # "true" | "false"
    expert_needed: Optional[str]  # Agent name or None
    routing_reason: Optional[str]  # Reason for routing

class ConversationalState(TypedDict):
    # Inputs
    message: str                           # current (simulated) member message or synthesized snippet
    chat_history: List[ChatMsg]         # full running conversation log
    member_state: Dict[str, Any]           # evolving facts (adherence, travel, labs...)
    week_index: int                        # current week (1-35)
    thread_index: int                      # current conversation thread within the week (1-5)
    message_in_thread: int                 # message count within current thread

    # Router
    pending_agents: List[str]              # queue selected this turn (e.g., ["Carla","DrWarren"])
    current_agent: Optional[str]

    # Member decision
    member_decision: Optional[str]         # "CONTINUE_CONVERSATION" | "END_TURN"

    # Event tracking
    active_events: List[EventObj]          # ongoing events that need follow-up
    completed_events: List[EventObj]       # historical events for reference

    # Outputs (per turn)
    agent_responses: List[AgentOutput]   # collected structured outputs from agents this turn
    new_thread_required: Optional[bool]