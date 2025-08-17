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

# New data structures for Decision Tracking System
class DecisionEvidence(TypedDict):
    evidence_type: str  # "test_result", "symptom_report", "member_feedback", "agent_observation"
    source: str  # Where the evidence came from
    description: str  # What the evidence shows
    confidence: float  # 0.0 to 1.0 confidence in this evidence
    timestamp: str  # When this evidence was collected
    relevance_score: float  # 0.0 to 1.0 how relevant this evidence is to the decision

class RiskAssessment(TypedDict):
    risk_factor: str  # What risk is being assessed
    risk_level: str  # "Low", "Medium", "High", "Critical"
    probability: float  # 0.0 to 1.0 probability of this risk occurring
    impact_severity: str  # "Low", "Medium", "High", "Critical"
    mitigation_strategy: Optional[str]  # How to reduce this risk
    notes: Optional[str]  # Additional context about the risk

class AgentAnalysis(TypedDict):
    agent_name: str  # Which agent performed the analysis
    analysis_type: str  # "initial_assessment", "follow_up", "specialist_review"
    key_findings: List[str]  # Main points from the analysis
    confidence_level: float  # 0.0 to 1.0 how confident the agent is
    recommendations: List[str]  # What the agent recommends
    concerns: List[str]  # Any concerns or red flags
    timestamp: str  # When this analysis was performed

class DecisionChain(TypedDict):
    decision_id: str  # Unique identifier for this decision
    triggering_event: str  # What prompted this decision
    member_id: str  # Which member this decision affects
    week_index: int  # When this decision was made
    priority: str  # "High", "Medium", "Low"
    status: str  # "pending", "in_progress", "implemented", "completed", "cancelled"
    
    # Decision making process
    agent_analyses: List[AgentAnalysis]  # All agent inputs
    evidence_considered: List[DecisionEvidence]  # All evidence gathered
    risk_assessments: List[RiskAssessment]  # All risks evaluated
    
    # Final decision
    final_decision: str  # What was decided
    decision_rationale: str  # Why this decision was made
    decision_maker: str  # Which agent made the final decision
    decision_timestamp: str  # When the decision was made
    
    # Outcome tracking
    implementation_status: str  # "not_started", "in_progress", "completed"
    outcome_metrics: Dict[str, Any]  # Measurable outcomes
    outcome_summary: Optional[str]  # Summary of how it turned out
    follow_up_required: bool  # Whether follow-up is needed
    next_review_date: Optional[str]  # When to review the outcome
    
    # Metadata
    created_at: str  # When this decision chain was created
    updated_at: str  # When it was last updated
    tags: List[str]  # Categories for filtering/searching

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
    
    # Decision Tracking System
    active_decision_chains: List[DecisionChain]  # Current decisions being processed
    completed_decision_chains: List[DecisionChain]  # Historical decisions for reference
    current_decision_context: Optional[DecisionChain]  # The decision being worked on in current turn