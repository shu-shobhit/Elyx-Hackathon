import os
import uuid
import random
from typing import Dict, Any
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from state import ConversationalState, ChatMsg, AgentOutput, EventObj
from typing import List
from datetime import datetime, timedelta

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
groq_api_key = os.getenv("GROQ_API_KEY")

def llm(model: str = "llama3-70b-8192", temperature: float = 0.5) -> ChatGroq:
    return ChatGroq(model=model, temperature=temperature, api_key=groq_api_key)

def calculate_conversation_timestamp(week_index: int, thread_index: int, message_in_thread: int) -> datetime:
    """
    Calculate a realistic timestamp for a message in the conversation.
    
    Args:
        week_index: Current week (1-35)
        thread_index: Current thread within the week (1-5)
        message_in_thread: Message number within the current thread
    
    Returns:
        datetime: Timestamp for the message
    """
    # Base start date: Monday, December 30th, 2024 at 10:00 AM
    base_week_start = datetime(2024, 12, 30, 10, 0, 0)
    
    # Calculate the start of the current week
    current_week_start = base_week_start + timedelta(weeks=week_index - 1)
    
    # Distribute threads across different days of the week
    # Thread 1: Monday, Thread 2: Tuesday, Thread 3: Wednesday, Thread 4: Thursday, Thread 5: Friday
    day_offset = thread_index - 1  # 0 for Monday, 1 for Tuesday, etc.
    thread_day = current_week_start + timedelta(days=day_offset)
    
    # Calculate thread start time within the day
    # Each thread starts at different times during the day (morning, afternoon, evening)
    hour_offsets = [10, 14, 16, 11, 15]  # 10 AM, 2 PM, 4 PM, 11 AM, 3 PM
    base_hour = hour_offsets[thread_index - 1] if thread_index <= 5 else 10
    
    # Add some randomization to the hour (±1 hour)
    hour_variation = random.uniform(-1, 1)
    thread_start = thread_day.replace(hour=base_hour) + timedelta(hours=hour_variation)
    
    # Calculate message timestamp within the thread
    # Messages are 2-6 minutes apart within a thread (randomized)
    message_minute_offset = message_in_thread * (3 + random.uniform(-1, 2))
    timestamp = thread_start + timedelta(minutes=message_minute_offset)
    
    return timestamp

def append_message(state: ConversationalState, role: str, agent: str, text: str, meta: Dict[str, Any] | None = None, event_id: str | None = None):
    # Get week and thread information from state
    week_index = state.get("week_index", 1)
    thread_index = state.get("thread_index", 1)
    message_in_thread = state.get("message_in_thread", 0)
    
    # Get the chat history to find the last timestamp
    history = state.get("chat_history", [])
    
    if history and message_in_thread > 0:
        # Get the last message's timestamp and add a delta
        last_timestamp_str = history[-1].get("timestamp", "")
        if last_timestamp_str:
            try:
                last_timestamp = datetime.fromisoformat(last_timestamp_str)
                # Add small time delta: 0-1 hours and 2-15 minutes to the last timestamp
                delta_hours = random.randint(0, 1)  # 0 to 1 hour
                delta_minutes = random.randint(2, 30)  # 2 to 15 minutes
                timestamp = last_timestamp + timedelta(hours=delta_hours, minutes=delta_minutes)
            except ValueError:
                # Fallback to calculated timestamp if parsing fails
                timestamp = calculate_conversation_timestamp(week_index, thread_index, message_in_thread)
        else:
            # Fallback to calculated timestamp
            timestamp = calculate_conversation_timestamp(week_index, thread_index, message_in_thread)
    else:
        # First message in thread - calculate the thread start time
        timestamp = calculate_conversation_timestamp(week_index, thread_index, message_in_thread)
    
    # Convert datetime to ISO format string for JSON serialization
    timestamp_str = timestamp.isoformat()
    
    msg = ChatMsg(
        role=role, 
        agent=agent, 
        text=text, 
        msg_id=str(uuid.uuid4()), 
        timestamp=timestamp_str,  # Store as string instead of datetime
        event_id=event_id,  # Optional event ID
        meta=meta or {}
    )
    
    history.append(msg)
    state["chat_history"] = history
    
    # Increment message counter for this thread
    state["message_in_thread"] = message_in_thread + 1

def generate_event_id(week_index: int, thread_index: int, event_type: str = "event") -> str:
    """Generate a unique event ID with semantic meaning"""
    unique_suffix = str(uuid.uuid4())[:8]
    return f"W{week_index}T{thread_index}_{event_type}_{unique_suffix}"

def create_event(state: ConversationalState, event_type: str, description: str, reason: str, 
                priority: str, created_by: str, meta: Dict[str, Any] | None = None) -> str:
    """Create a new event and add it to active events"""
    from datetime import datetime
    
    week_index = state.get("week_index", 1)
    thread_index = state.get("thread_index", 1)
    
    event_id = generate_event_id(week_index, thread_index, event_type)
    
    event = EventObj(
        event_id=event_id,
        Type=event_type,
        description=description,
        reason=reason,
        priority=priority,
        status="proposed",
        created_by=created_by,
        created_at=datetime.now().isoformat(),
        meta=meta or {}
    )
    
    active_events = state.get("active_events", [])
    active_events.append(event)
    state["active_events"] = active_events
    
    return event_id

def update_event_status(state: ConversationalState, event_id: str, new_status: str) -> bool:
    """Update the status of an active event"""
    active_events = state.get("active_events", [])
    
    for event in active_events:
        if event["event_id"] == event_id:
            event["status"] = new_status
            
            # Move to completed events if status indicates completion
            if new_status in ["completed", "cancelled"]:
                active_events.remove(event)
                completed_events = state.get("completed_events", [])
                completed_events.append(event)
                state["completed_events"] = completed_events
                state["active_events"] = active_events
            
            return True
    
    return False

def get_active_events_by_type(state: ConversationalState, event_type: str) -> List[EventObj]:
    """Get all active events of a specific type"""
    active_events = state.get("active_events", [])
    return [event for event in active_events if event["Type"] == event_type]

def append_agent_response(state: ConversationalState, payload: Dict[str, Any]):
    responses = state.get("agent_responses", [])
    responses.append(AgentOutput(**payload))
    state["agent_responses"] = responses
