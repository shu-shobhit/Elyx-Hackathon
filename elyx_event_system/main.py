# main.py
import json
from orchestrator import build_graph
from state import ConversationalState
from initialization import create_initial_conversational_state
from pprint import pprint
import random
from datetime import datetime

def main():
    # Initialize the conversation graph
    graph = build_graph()
    
    # Initialize the overall conversation state
    all_conversations = []
    
    print("=== Starting 35-Week Health Coaching Simulation ===")
    print("Each week will have 5 conversation threads")
    print("Threads are distributed across different days of the week")
    print("Starting from December 30th, 2024 (Monday) at 10:00 AM")
    print("=" * 60)
    
    # Initialize the persistent state with member onboarding (ONCE ONLY)
    persistent_state = create_initial_conversational_state()
    
    # Outer loop: 35 weeks
    for week in range(1, 2):
        print(f"\n📅 WEEK {week} - Starting new week of conversation")
        print("-" * 40)
        
        # Update the week index in the persistent state
        persistent_state["week_index"] = week
        
        # Inner loop: 5 conversation threads per week (on average)
        threads_this_week = random.randint(2,3)  # You can make this random if needed
        
        for thread in range(1, threads_this_week + 1):
            print(f"\n💬 Thread {thread}/{threads_this_week} - Week {week}")
            print("-" * 30)
            
            # Update thread index and reset message counter for this thread
            persistent_state["thread_index"] = thread
            persistent_state["message_in_thread"] = 0
            
            # Create a copy of the current state for this thread execution
            thread_state = persistent_state.copy()
            
            try:
                # Execute this conversation thread
                for output in graph.stream(thread_state, config={"recursion_limit": 150}):
                    # The 'output' dictionary contains the state after each node has run
                    last_node = list(output.keys())[-1]
                    # Uncomment below if you want to see node execution details
                    # print(f"  Node '{last_node}' completed")
                
                # Get the final state after the thread is complete
                final_state = output[last_node]
                
                # Update the persistent state with the results from this thread
                # This ensures continuity across threads and weeks
                persistent_state.update(final_state)
                
            except Exception as e:
                print(f"  ❌ Error in thread {thread}: {e}")
                import traceback
                traceback.print_exc()
            
    print("\n\n" + "=" * 80)
    print("📋 COMPLETE 35-WEEK CONVERSATION LOG")
    print("=" * 80)
    
    for i, msg in enumerate(persistent_state.get('chat_history')):
        sender = msg.get('agent') or msg.get('role', 'unknown')
        text = msg.get('text', '')
        timestamp = msg.get('timestamp')
        
        if timestamp:
            # Parse ISO format string back to datetime for display
            try:
                dt = datetime.fromisoformat(timestamp)
                time_str = dt.strftime("%a, %b %d, %I:%M %p")
            except ValueError:
                time_str = timestamp  # Fallback to raw string if parsing fails
            print(f"{i+1:3d}. [{time_str}] [{sender.upper()}]: {text}")
        else:
            print(f"{i+1:3d}. [{sender.upper()}]: {text}")
    
    print(f"\n🎉 Simulation Complete!")
    print(f"📊 Total messages: {len(persistent_state.get('chat_history', []))}")
    print(f"📅 Duration: 35 weeks")
    print(f"💬 Total threads: {35 * 5}")
    print(f"👤 Final member state: {persistent_state.get('member_state', {})}")
    print(f"📅 Active events: {len(persistent_state.get('active_events', []))}")
    print(f"✅ Completed events: {len(persistent_state.get('completed_events', []))}")
    
    # Decision Tracking Summary
    active_decisions = len(persistent_state.get('active_decision_chains', []))
    completed_decisions = len(persistent_state.get('completed_decision_chains', []))
    print(f"🎯 Decision Tracking:")
    print(f"   📋 Active decision chains: {active_decisions}")
    print(f"   ✅ Completed decision chains: {completed_decisions}")
    print(f"   📊 Total decisions tracked: {active_decisions + completed_decisions}")
    
    # Show detailed decision chain information
    if active_decisions > 0 or completed_decisions > 0:
        print(f"\n" + "="*80)
        print("📋 DECISION CHAINS DETAILED SUMMARY")
        print("="*80)
        
        # Show active decision chains
        active_chains = persistent_state.get('active_decision_chains', [])
        if active_chains:
            print(f"\n🔄 ACTIVE DECISION CHAINS ({len(active_chains)}):")
            for i, chain in enumerate(active_chains, 1):
                print(f"\n  {i}. Decision ID: {chain.get('decision_id', 'N/A')}")
                print(f"     Trigger: {chain.get('triggering_event', 'N/A')}")
                print(f"     Member: {chain.get('member_id', 'N/A')}")
                print(f"     Week: {chain.get('week_index', 'N/A')}")
                print(f"     Status: {chain.get('status', 'N/A')}")
                print(f"     Created: {chain.get('created_at', 'N/A')}")
                
                # Show agent analyses
                agent_analyses = chain.get('agent_analyses', [])
                if agent_analyses:
                    print(f"     Agents involved ({len(agent_analyses)}):")
                    for analysis in agent_analyses:
                        agent_name = analysis.get('agent_name', 'N/A')
                        analysis_type = analysis.get('analysis_type', 'N/A')
                        confidence = analysis.get('confidence_level', 0)
                        recommendations = analysis.get('recommendations', [])
                        print(f"       - {agent_name} ({analysis_type}): {confidence:.1%} confidence")
                        if recommendations:
                            print(f"         Recommendations: {', '.join(recommendations[:2])}{'...' if len(recommendations) > 2 else ''}")
        
        # Show completed decision chains
        completed_chains = persistent_state.get('completed_decision_chains', [])
        if completed_chains:
            print(f"\n✅ COMPLETED DECISION CHAINS ({len(completed_chains)}):")
            for i, chain in enumerate(completed_chains, 1):
                print(f"\n  {i}. Decision ID: {chain.get('decision_id', 'N/A')}")
                print(f"     Trigger: {chain.get('triggering_event', 'N/A')}")
                print(f"     Member: {chain.get('member_id', 'N/A')}")
                print(f"     Week: {chain.get('week_index', 'N/A')}")
                print(f"     Final Decision: {chain.get('final_decision', 'N/A')}")
                print(f"     Decision Maker: {chain.get('decision_maker', 'N/A')}")
                print(f"     Completed: {chain.get('decision_timestamp', 'N/A')}")
                print(f"     Outcome: {chain.get('outcome', 'N/A')}")
                
                # Show agent analyses
                agent_analyses = chain.get('agent_analyses', [])
                if agent_analyses:
                    print(f"     Agents involved ({len(agent_analyses)}):")
                    for analysis in agent_analyses:
                        agent_name = analysis.get('agent_name', 'N/A')
                        analysis_type = analysis.get('analysis_type', 'N/A')
                        confidence = analysis.get('confidence_level', 0)
                        recommendations = analysis.get('recommendations', [])
                        print(f"       - {agent_name} ({analysis_type}): {confidence:.1%} confidence")
                        if recommendations:
                            print(f"         Recommendations: {', '.join(recommendations[:2])}{'...' if len(recommendations) > 2 else ''}")
        
        # Show decision statistics
        print(f"\n📊 DECISION TRACKING STATISTICS:")
        
        # Count by agent
        all_chains = active_chains + completed_chains
        agent_participation = {}
        total_confidence = 0
        confidence_count = 0
        
        for chain in all_chains:
            agent_analyses = chain.get('agent_analyses', [])
            for analysis in agent_analyses:
                agent_name = analysis.get('agent_name', 'Unknown')
                agent_participation[agent_name] = agent_participation.get(agent_name, 0) + 1
                
                confidence = analysis.get('confidence_level', 0)
                total_confidence += confidence
                confidence_count += 1
        
        if agent_participation:
            print(f"   Agent Participation:")
            for agent, count in agent_participation.items():
                print(f"     - {agent}: {count} decisions")
        
        if confidence_count > 0:
            avg_confidence = total_confidence / confidence_count
            print(f"   Average Confidence: {avg_confidence:.1%}")
        
        # Count by week
        week_counts = {}
        for chain in all_chains:
            week = chain.get('week_index', 'Unknown')
            week_counts[week] = week_counts.get(week, 0) + 1
        
        if week_counts:
            print(f"   Decisions by Week:")
            for week in sorted(week_counts.keys()):
                print(f"     - Week {week}: {week_counts[week]} decisions")
    
    print("=" * 80)

if __name__ == "__main__":
    main()