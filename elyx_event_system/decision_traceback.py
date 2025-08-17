#!/usr/bin/env python3
"""
Decision Traceback Utilities
Functions to query and analyze decision chains for traceability.
"""

from typing import List, Dict, Any, Optional
from state import ConversationalState

def get_decision_by_id(state: ConversationalState, decision_id: str) -> Optional[Dict[str, Any]]:
    """Get a specific decision chain by its ID"""
    # Check active chains first
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        if chain.get("decision_id") == decision_id:
            return chain
    
    # Check completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        if chain.get("decision_id") == decision_id:
            return chain
    
    return None

def get_member_decision_history(state: ConversationalState, member_name: str) -> List[Dict[str, Any]]:
    """Get all decision chains for a specific member"""
    all_decisions = []
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        if chain.get("member_id") == member_name:
            all_decisions.append(chain)
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        if chain.get("member_id") == member_name:
            all_decisions.append(chain)
    
    return all_decisions

def get_decisions_by_week(state: ConversationalState, week_index: int) -> List[Dict[str, Any]]:
    """Get all decision chains from a specific week"""
    all_decisions = []
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        if chain.get("week_index") == week_index:
            all_decisions.append(chain)
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        if chain.get("week_index") == week_index:
            all_decisions.append(chain)
    
    return all_decisions

def get_decisions_by_agent(state: ConversationalState, agent_name: str) -> List[Dict[str, Any]]:
    """Get all decision chains involving a specific agent"""
    all_decisions = []
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        agent_analyses = chain.get("agent_analyses", [])
        if any(analysis.get("agent_name") == agent_name for analysis in agent_analyses):
            all_decisions.append(chain)
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        agent_analyses = chain.get("agent_analyses", [])
        if any(analysis.get("agent_name") == agent_name for analysis in agent_analyses):
            all_decisions.append(chain)
    
    return all_decisions

def get_decisions_by_confidence(state: ConversationalState, min_confidence: float = 0.8) -> List[Dict[str, Any]]:
    """Get decision chains with confidence above threshold"""
    all_decisions = []
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        agent_analyses = chain.get("agent_analyses", [])
        if any(analysis.get("confidence_level", 0) >= min_confidence for analysis in agent_analyses):
            all_decisions.append(chain)
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        agent_analyses = chain.get("agent_analyses", [])
        if any(analysis.get("confidence_level", 0) >= min_confidence for analysis in agent_analyses):
            all_decisions.append(chain)
    
    return all_decisions

def search_decisions_by_intervention(state: ConversationalState, intervention: str) -> List[Dict[str, Any]]:
    """Search for decision chains that include a specific intervention (medication, test, etc.)"""
    all_decisions = []
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            interventions = analysis.get("interventions", [])
            if intervention in interventions:
                all_decisions.append(chain)
                break
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            interventions = analysis.get("interventions", [])
            if intervention in interventions:
                all_decisions.append(chain)
                break
    
    return all_decisions

def search_decisions_by_keyword(state: ConversationalState, keyword: str) -> List[Dict[str, Any]]:
    """Search for decision chains containing specific keywords"""
    all_decisions = []
    keyword_lower = keyword.lower()
    
    # Get active chains
    active_chains = state.get("active_decision_chains", [])
    for chain in active_chains:
        # Search in triggering event
        if keyword_lower in chain.get("triggering_event", "").lower():
            all_decisions.append(chain)
            continue
        
        # Search in agent analyses
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            analysis_text = " ".join(analysis.get("analysis", []))
            if keyword_lower in analysis_text.lower():
                all_decisions.append(chain)
                break
    
    # Get completed chains
    completed_chains = state.get("completed_decision_chains", [])
    for chain in completed_chains:
        # Search in triggering event
        if keyword_lower in chain.get("triggering_event", "").lower():
            all_decisions.append(chain)
            continue
        
        # Search in agent analyses
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            analysis_text = " ".join(analysis.get("analysis", []))
            if keyword_lower in analysis_text.lower():
                all_decisions.append(chain)
                break
    
    return all_decisions

def get_active_decisions(state: ConversationalState) -> List[Dict[str, Any]]:
    """Get all active (in-progress) decision chains"""
    return state.get("active_decision_chains", [])

def get_completed_decisions(state: ConversationalState) -> List[Dict[str, Any]]:
    """Get all completed decision chains"""
    return state.get("completed_decision_chains", [])

def format_decision_summary(decision: Dict[str, Any]) -> str:
    """Format a decision chain into a readable summary"""
    summary = f"""
**Decision Chain: {decision.get('decision_id', 'N/A')}**
- **Trigger**: {decision.get('triggering_event', 'N/A')}
- **Member**: {decision.get('member_id', 'N/A')}
- **Status**: {decision.get('status', 'N/A')}
- **Created**: {decision.get('created_at', 'N/A')}

**Agents Involved**:"""
    
    agent_analyses = decision.get("agent_analyses", [])
    for analysis in agent_analyses:
        summary += f"""
  - **{analysis.get('agent_name', 'N/A')}** ({analysis.get('analysis_type', 'N/A')})
    - Confidence: {analysis.get('confidence_level', 0):.1%}
    - Recommendations: {', '.join(analysis.get('recommendations', []))}"""
    
    if decision.get("final_decision"):
        summary += f"""
**Final Decision**: {decision.get('final_decision', 'N/A')}
**Outcome**: {decision.get('outcome', 'N/A')}"""
    
    return summary

def get_decision_statistics(state: ConversationalState) -> Dict[str, Any]:
    """Get statistics about all decision chains"""
    active_chains = state.get("active_decision_chains", [])
    completed_chains = state.get("completed_decision_chains", [])
    
    total_decisions = len(active_chains) + len(completed_chains)
    
    # Count by agent
    agent_counts = {}
    for chain in active_chains + completed_chains:
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            agent_name = analysis.get("agent_name", "Unknown")
            agent_counts[agent_name] = agent_counts.get(agent_name, 0) + 1
    
    # Average confidence
    total_confidence = 0
    confidence_count = 0
    for chain in active_chains + completed_chains:
        agent_analyses = chain.get("agent_analyses", [])
        for analysis in agent_analyses:
            confidence = analysis.get("confidence_level", 0)
            total_confidence += confidence
            confidence_count += 1
    
    avg_confidence = total_confidence / confidence_count if confidence_count > 0 else 0
    
    return {
        "total_decisions": total_decisions,
        "active_decisions": len(active_chains),
        "completed_decisions": len(completed_chains),
        "agent_participation": agent_counts,
        "average_confidence": avg_confidence
    }
