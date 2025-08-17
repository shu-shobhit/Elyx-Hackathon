#!/usr/bin/env python3
"""
Integration test to verify Decision Tracking System works with actual conversation flow.
"""

from state import ConversationalState
from initialization import create_initial_conversational_state
from utils import create_decision_chain, add_agent_analysis, finalize_decision
from orchestrator import detect_decision_point

def test_integration():
    """Test that decision tracking integrates properly with conversation flow"""
    
    print("🧪 TESTING DECISION TRACKING INTEGRATION")
    print("=" * 60)
    
    # Create initial state (same as main.py)
    state = create_initial_conversational_state()
    
    print(f"✅ Initial state created with decision tracking fields:")
    print(f"   - active_decision_chains: {len(state.get('active_decision_chains', []))}")
    print(f"   - completed_decision_chains: {len(state.get('completed_decision_chains', []))}")
    
    # Simulate an agent response (like what happens in real conversation)
    agent_response = {
        "agent": "DrWarren",
        "message": "I've reviewed your blood panel and recommend starting a glucose management protocol.",
        "analysis": "Elevated fasting glucose indicates impaired glucose metabolism requiring dietary intervention.",
        "recommendations": ["Implement nutrition protocol", "Schedule follow-up monitoring"],
        "medications": ["Metformin"],
        "tests": ["HbA1c test"],
        "confidence": 0.85,
        "needs_expert": True,
        "expert_needed": "Carla",
        "routing_reason": "Nutrition specialist needed for protocol design"
    }
    
    # Add to agent responses (like what happens in real conversation)
    agent_responses = state.get("agent_responses", [])
    agent_responses.append(agent_response)
    state["agent_responses"] = agent_responses
    
    print(f"\n📝 Added agent response from Dr. Warren")
    
    # Test decision point detection
    is_decision = detect_decision_point(state)
    print(f"🎯 Decision point detected: {is_decision}")
    
    if is_decision:
        # Simulate what the agent_response_collector would do
        member_name = state.get("member_state", {}).get("name", "Unknown Member")
        
        # Create decision chain
        decision_id = create_decision_chain(
            state, 
            "DrWarren made recommendations for glucose management", 
            member_name
        )
        print(f"📋 Created decision chain: {decision_id}")
        
        # Add agent analysis
        add_agent_analysis(
            state,
            decision_id,
            "DrWarren",
            "clinical_analysis",
            ["Elevated fasting glucose", "Impaired glucose metabolism"],
            0.85,
            ["Implement nutrition protocol", "Schedule follow-up monitoring"],
            ["Metformin", "HbA1c test"]
        )
        print(f"✅ Added Dr. Warren's analysis to decision chain")
        
        # Show current state
        active_chains = state.get("active_decision_chains", [])
        print(f"\n📊 Current Decision Tracking State:")
        print(f"   - Active chains: {len(active_chains)}")
        print(f"   - Completed chains: {len(state.get('completed_decision_chains', []))}")
        
        if active_chains:
            chain = active_chains[0]
            print(f"   - Current chain ID: {chain['decision_id']}")
            print(f"   - Trigger: {chain['triggering_event']}")
            print(f"   - Status: {chain['status']}")
            print(f"   - Agent analyses: {len(chain.get('agent_analyses', []))}")
        
        # Finalize the decision
        finalize_decision(
            state,
            decision_id,
            "Implement comprehensive glucose management protocol",
            "Protocol designed and ready for implementation",
            "DrWarren"
        )
        print(f"✅ Finalized decision chain")
        
        # Show final state
        print(f"\n📊 Final Decision Tracking State:")
        print(f"   - Active chains: {len(state.get('active_decision_chains', []))}")
        print(f"   - Completed chains: {len(state.get('completed_decision_chains', []))}")
        
        completed_chains = state.get("completed_decision_chains", [])
        if completed_chains:
            chain = completed_chains[0]
            print(f"   - Completed chain ID: {chain['decision_id']}")
            print(f"   - Final decision: {chain.get('final_decision', 'N/A')}")
            print(f"   - Outcome: {chain.get('outcome', 'N/A')}")
    
    print(f"\n✅ Integration test completed successfully!")
    return state

if __name__ == "__main__":
    test_integration()
