from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator

class ChatMsg(TypedDict):
    role: str       # "member" | "ruby" | "dr_warren" | ...
    agent: str      # Agent key when role is an Elyx team member
    text: str       # WhatsApp-style message text
    turn_id: str    # Optional: UUID / trace id
    meta: Dict[str, Any]

class EventObj(TypedDict):
    Type: str
    description: str
    reason: str
    priority: str    # "High" | "Medium" | "Low"
    meta: Dict[str, Any]

class AgentOutput(TypedDict):
    agent: str 
    message: str
    proposed_event: Optional[EventObj]

class ConversationalState(TypedDict):
    # Inputs
    message: str                           # current (simulated) member message or synthesized snippet
    chat_history: Annotated[List[ChatMsg], operator.add]            # full running conversation log
    member_state: Dict[str, Any]           # evolving facts (adherence, travel, labs...)
    week_index: int                        # optional – for scheduled rules

    # Router
    pending_agents: List[str]              # queue selected this turn (e.g., ["Carla","DrWarren"])
    current_agent: Optional[str]

    # Outputs (per turn)
    agent_responses: List[AgentOutput]     # collected structured outputs from agents this turn
