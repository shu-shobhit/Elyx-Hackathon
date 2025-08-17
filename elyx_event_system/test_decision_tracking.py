#!/usr/bin/env python3
"""
Test script to demonstrate the Decision Tracking System functionality.
This script simulates a conversation where agents make decisions and shows how
the system automatically tracks decision chains.
"""

import json
from datetime import datetime
from state import ConversationalState
from utils import create_decision_chain, add_agent_analysis, add_evidence, finalize_decision, get_completed_decision_chains
from orchestrator import detect_decision_point

def simulate_agent_response(state: ConversationalState, agent_name: str, message: str, 
                          analysis: str, recommendations: list, medications: list = None, 
                          tests: list = None, confidence: float = 0.8):
    """Simulate an agent response with decision tracking data"""
    
    # Create the agent response payload
    payload = {
        "agent": agent_name,
        "message": message,
        "analysis": analysis,
        "recommendations": recommendations,
        "medications": medications or [],
        "tests": tests or [],
        "confidence": confidence,
        "needs_expert": False,
        "expert_needed": None,
        "routing_reason": None,
        "proposed_event": None
    }
    
    # Add to agent responses
    agent_responses = state.get("agent_responses", [])
    agent_responses.append(payload)
    state["agent_responses"] = agent_responses
    
    return state

def print_decision_chains(state: ConversationalState):
    """Print all decision chains in a readable format"""
    print("\n" + "="*80)
    print("DECISION TRACKING SYSTEM - CURRENT STATE")
    print("="*80)
    
    # Print active decision chains
    active_chains = state.get("active_decision_chains", [])
    if active_chains:
        print(f"\n📋 ACTIVE DECISION CHAINS ({len(active_chains)}):")
        for i, chain in enumerate(active_chains, 1):
            print(f"\n  {i}. Decision ID: {chain['decision_id']}")
            print(f"     Trigger: {chain['triggering_event']}")
            print(f"     Member: {chain['member_id']}")
            print(f"     Status: {chain['status']}")
            print(f"     Created: {chain['created_at']}")
            
            if chain.get('agent_analyses'):
                print(f"     Agent Analyses ({len(chain['agent_analyses'])}):")
                for analysis in chain['agent_analyses']:
                    print(f"       - {analysis['agent_name']}: {analysis['analysis_type']}")
                    print(f"         Confidence: {analysis['confidence_level']}")
                    print(f"         Recommendations: {analysis['recommendations']}")
    
    # Print completed decision chains
    completed_chains = state.get("completed_decision_chains", [])
    if completed_chains:
        print(f"\n✅ COMPLETED DECISION CHAINS ({len(completed_chains)}):")
        for i, chain in enumerate(completed_chains, 1):
            print(f"\n  {i}. Decision ID: {chain['decision_id']}")
            print(f"     Trigger: {chain['triggering_event']}")
            print(f"     Final Decision: {chain.get('final_decision', 'N/A')}")
            print(f"     Completed: {chain.get('decision_timestamp', 'N/A')}")
            print(f"     Outcome: {chain.get('outcome', 'N/A')}")

def test_decision_tracking():
    """Test the decision tracking system with a simulated conversation"""
    
    print("🧪 TESTING DECISION TRACKING SYSTEM")
    print("="*80)
    
    # Initialize state
    state = ConversationalState({
        "week_index": 1,
        "member_state": {"name": "Rohan Patel"},
        "agent_responses": [],
        "active_decision_chains": [],
        "completed_decision_chains": []
    })
    
    print("\n📝 SCENARIO: Member asks about elevated glucose levels")
    print("-" * 60)
    
    # Simulate Dr. Warren making a medical decision
    print("\n1️⃣ Dr. Warren analyzes glucose levels and makes recommendations...")
    state = simulate_agent_response(
        state=state,
        agent_name="DrWarren",
        message="Rohan, I've reviewed your latest blood panel. Your fasting glucose is elevated at 105 mg/dL, which indicates impaired glucose metabolism. This requires immediate intervention through dietary modification to improve insulin sensitivity and prevent progression to diabetes.",
        analysis="Elevated fasting glucose (105 mg/dL) indicates impaired glucose metabolism. This requires immediate intervention through dietary modification to improve insulin sensitivity and prevent progression to diabetes.",
        recommendations=["Implement nutrition protocol for glucose management", "Schedule follow-up glucose monitoring"],
        tests=["Follow-up fasting glucose in 3 months"],
        confidence=0.85
    )
    
    # Check if decision point is detected
    is_decision_point = detect_decision_point(state)
    print(f"   Decision point detected: {is_decision_point}")
    
    # Simulate the orchestrator creating a decision chain
    if is_decision_point:
        print("   Creating decision chain...")
        decision_id = create_decision_chain(
            state, 
            "DrWarren made recommendations for glucose management", 
            "Rohan Patel"
        )
        print(f"   Decision chain created: {decision_id}")
        
        # Add Dr. Warren's analysis to the decision chain
        add_agent_analysis(
            state,
            decision_id,
            "DrWarren",
            "clinical_analysis",
            ["Elevated fasting glucose (105 mg/dL)", "Impaired glucose metabolism", "Requires dietary intervention"],
            0.85,
            ["Implement nutrition protocol for glucose management", "Schedule follow-up glucose monitoring"],
            ["Risk of diabetes progression"]
        )
        print("   Dr. Warren's analysis added to decision chain")
    
    print_decision_chains(state)
    
    # Simulate Carla adding her nutrition expertise
    print("\n2️⃣ Carla adds nutrition protocol details...")
    state = simulate_agent_response(
        state=state,
        agent_name="Carla",
        message="Based on Dr. Warren's clinical assessment, I'll design a targeted nutrition protocol focusing on low glycemic index foods, increased fiber intake, and strategic meal timing to improve insulin sensitivity.",
        analysis="Nutritional intervention for impaired glucose metabolism requires low glycemic index foods, increased fiber (25-30g daily), and strategic meal timing to stabilize blood sugar levels.",
        recommendations=["Implement low glycemic index diet", "Increase fiber intake to 25-30g daily", "Add strategic meal timing"],
        confidence=0.9
    )
    
    # Add Carla's analysis to the current decision chain
    active_chains = state.get("active_decision_chains", [])
    if active_chains:
        current_chain = active_chains[0]
        add_agent_analysis(
            state,
            current_chain["decision_id"],
            "Carla",
            "nutritional_analysis",
            ["Low glycemic index foods required", "Increased fiber intake (25-30g daily)", "Strategic meal timing needed"],
            0.9,
            ["Implement low glycemic index diet", "Increase fiber intake to 25-30g daily", "Add strategic meal timing"],
            ["Compliance challenges with dietary changes"]
        )
        print("   Carla's analysis added to decision chain")
    
    print_decision_chains(state)
    
    # Simulate adding evidence
    print("\n3️⃣ Adding evidence to the decision chain...")
    if active_chains:
        current_chain = active_chains[0]
        add_evidence(
            state,
            current_chain["decision_id"],
            "test_results",
            "Blood Panel",
            "Fasting glucose: 105 mg/dL (elevated)",
            0.95,
            0.9
        )
        add_evidence(
            state,
            current_chain["decision_id"],
            "member_feedback",
            "Member Report",
            "Member reports feeling tired after meals",
            0.8,
            0.7
        )
        print("   Evidence added to decision chain")
    
    print_decision_chains(state)
    
    # Simulate finalizing the decision
    print("\n4️⃣ Finalizing the decision chain...")
    if active_chains:
        current_chain = active_chains[0]
        finalize_decision(
            state,
            current_chain["decision_id"],
            "Implement comprehensive nutrition protocol for glucose management",
            "Protocol designed and ready for implementation",
            "DrWarren"
        )
        print("   Decision chain finalized")
    
    print_decision_chains(state)
    
    # Show completed decision chains
    completed_chains = get_completed_decision_chains(state)
    if completed_chains:
        print(f"\n📊 DECISION TRACKING SUMMARY:")
        print(f"   Total decisions tracked: {len(completed_chains)}")
        for chain in completed_chains:
            print(f"   - {chain['decision_id']}: {chain['triggering_event']}")
            print(f"     Final decision: {chain.get('final_decision', 'N/A')}")
            print(f"     Agents involved: {[a['agent_name'] for a in chain.get('agent_analyses', [])]}")
    
    print("\n✅ Decision Tracking System Test Complete!")
    return state

if __name__ == "__main__":
    test_decision_tracking()
