# main.py
import json
from typing import Dict, Any
from orchestrator import build_graph
from state import ConversationalState

def main():
    # Initialize the conversation graph
    graph = build_graph()
    
    # Example initial state
    initial_state: ConversationalState = {
        "message": "I've been feeling tired lately and my sleep has been poor. Can you help me figure out what's going on?",
        "chat_history": [],
        "member_state": {
            "name": "John Doe",
            "week_index": 1,
            "has_whoop": True,
            "has_cgm": False
        },
        "week_index": 1,
        "pending_agents": [],
        "current_agent": None,
        "agent_responses": []
    }
    
    print(f"Initial state: {initial_state}")
    
    # Run the conversation
    print("Invoking conversation graph...")
    try:
        result = graph.invoke(initial_state)
        print("Conversation completed successfully!")
        print(f"Final state keys: {list(result.keys())}")
        print(f"Agent responses: {len(result.get('agent_responses', []))}")
        
        # Print the responses
        for i, response in enumerate(result.get('agent_responses', [])):
            print(f"\n--- Response {i+1} ---")
            print(f"Agent: {response.get('agent')}")
            print(f"Message: {response.get('message')}")
            if response.get('proposed_event'):
                print(f"Event: {response.get('proposed_event')}")
                
    except Exception as e:
        print(f"Error running conversation: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
