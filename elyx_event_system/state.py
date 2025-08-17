# state.py
from typing import TypedDict, List, Dict, Any, Optional, Annotated
import operator
from pprint import pprint

class ChatMsg(TypedDict):
    role: str       # "member" | "ruby" | "dr_warren" | ... 
    agent: Optional[str]   # Agent key when role is an Elyx team member
    text: str       # WhatsApp-style message text
    msg_id: str
    meta: Optional[Dict[str, Any]]

class EventObj(TypedDict):
    Type: str
    description: str
    reason: str
    priority: str    # "High" | "Medium" | "Low"
    meta: Dict[str, Any]

class AgentOutput(TypedDict, total=False):
    agent: str 
    message: str
    proposed_event: Optional[EventObj]
    needs_expert: Optional[str]  # "true" | "false"
    expert_needed: Optional[str]  # Agent name or None
    routing_reason: Optional[str]  # Reason for routing

# New data structures for comprehensive test panel results
class TestResult(TypedDict):
    test_name: str
    value: Any
    unit: Optional[str]
    reference_range: Optional[str]
    status: str  # "Normal", "Abnormal", "Borderline", "Critical"
    interpretation: Optional[str]
    date: str

class TestCategory(TypedDict):
    category_name: str
    tests: List[TestResult]
    summary: str
    risk_level: str  # "Low", "Medium", "High"
    recommendations: List[str]

class TestPanelResults(TypedDict):
    test_date: str
    week_index: int
    overall_health_score: float  # 0.0 to 1.0
    risk_factors: List[str]
    categories: List[TestCategory]
    summary: str
    next_assessment_due: str  # Date for next 3-month assessment
    specialist_recommendations: Dict[str, List[str]]  # Agent name -> recommendations

class ConversationalState(TypedDict):
    # Inputs
    message: str                           # current (simulated) member message or synthesized snippet
    chat_history: List[ChatMsg]         # full running conversation log
    member_state: Dict[str, Any]           # evolving facts (adherence, travel, labs...)
    week_index: int                        # optional – for scheduled rules

    # Router
    pending_agents: List[str]              # queue selected this turn (e.g., ["Carla","DrWarren"])
    current_agent: Optional[str]

    # Member decision
    member_decision: Optional[str]         # "CONTINUE_CONVERSATION" | "END_TURN"

    # Outputs (per turn)
    agent_responses: List[AgentOutput]   # collected structured outputs from agents this turn
    
    # Test Panel Results (NEW SECTION)
    last_test_panel: Optional[TestPanelResults]  # Results from the most recent comprehensive assessment
