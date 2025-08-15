import os
import uuid
from typing import Dict, Any
from langchain_groq import ChatGroq
from dotenv import load_dotenv
from state import ConversationalState

load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '..', '.env'))
groq_api_key = os.getenv("GROQ_API_KEY")

def llm(model: str = "llama3-70b-8192", temperature: float = 0.4) -> ChatGroq:
    # Single place to control model/temperature. Swap providers here if needed.
    return ChatGroq(model=model, temperature=temperature, api_key=groq_api_key)

def append_message(state: ConversationalState, role: str, agent: str, text: str, meta: Dict[str, Any] | None = None):
    msg = {"role": role, "agent": agent, "text": text, "turn_id": str(uuid.uuid4()), "meta": meta or {}}
    history = state.get("chat_history", [])
    history.append(msg)
    state["chat_history"] = history

def append_agent_response(state: ConversationalState, payload: Dict[str, Any]):
    responses = state.get("agent_responses", [])
    responses.append(payload)
    state["agent_responses"] = responses
