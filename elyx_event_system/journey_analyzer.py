#!/usr/bin/env python3
"""
Member Journey Analysis System
Extracts episodes, persona changes, and metrics from existing conversation data
"""

import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import pandas as pd
import numpy as np
from state import ConversationalState, ChatMsg, DecisionChain, AgentOutput

@dataclass
class Episode:
    """Represents a distinct health journey episode"""
    episode_id: str
    title: str
    start_date: str
    end_date: str
    duration_days: int
    week_range: Tuple[int, int]
    
    # Core episode data
    trigger_type: str  # "member_initiated", "agent_initiated", "system_scheduled"
    trigger_description: str
    triggered_by: str  # Member or agent name
    
    # Conversation flow
    messages: List[ChatMsg]
    agents_involved: List[str]
    message_count: int
    
    # Outcomes
    final_outcome: str
    outcome_type: str  # "information_provided", "plan_proposed", "intervention_scheduled", "issue_resolved"
    friction_points: List[str]
    
    # Metrics
    response_time_minutes: Optional[float]
    time_to_resolution_hours: Optional[float]
    agent_switches: int
    member_satisfaction_indicators: List[str]
    
    # Enhanced data
    recommendations: List[str] = None
    decision_id: Optional[str] = None
    medications: List[str] = None  
    tests: List[str] = None

@dataclass
class PersonaState:
    """Member's persona state at a specific point in time"""
    timestamp: str
    week_index: int
    
    # Core persona attributes
    engagement_level: str  # "high", "medium", "low"
    health_awareness: str  # "proactive", "reactive", "passive"
    communication_style: str  # "detailed", "brief", "question_heavy"
    trust_level: str  # "high", "building", "skeptical"
    
    # Health status perception
    perceived_health_status: str
    primary_concerns: List[str]
    confidence_in_plan: float  # 0.0 to 1.0
    
    # Behavioral indicators
    initiative_taking: bool
    data_sharing_willingness: str  # "open", "selective", "reluctant"
    follow_through_likelihood: float  # 0.0 to 1.0

@dataclass
class InternalMetrics:
    """Internal operational metrics for a time period"""
    week_index: int
    
    # Agent activity metrics
    agent_hours: Dict[str, float]  # agent_name -> estimated hours
    consultation_count: Dict[str, int]  # agent_name -> number of consultations
    response_times: Dict[str, List[float]]  # agent_name -> response times in minutes
    
    # Decision quality metrics
    decision_confidence_avg: float
    decision_implementation_rate: float
    decision_revision_count: int
    
    # Member engagement metrics
    member_initiative_messages: int
    member_response_rate: float
    member_question_complexity: float  # 1.0 to 5.0

class JourneyAnalyzer:
    """Analyzes member journey from conversation data"""
    
    def __init__(self):
        self.episodes: List[Episode] = []
        self.persona_states: List[PersonaState] = []
        self.metrics: List[InternalMetrics] = []
    
    def analyze_journey(self, checkpoint_files: List[str]) -> Dict[str, Any]:
        """Main analysis function - processes all checkpoint files"""
        all_states = []
        
        # Load all checkpoint data
        for file_path in checkpoint_files:
            with open(file_path, 'r') as f:
                checkpoint = json.load(f)
                all_states.append(checkpoint['state'])
        
        # Extract episodes
        self.episodes = self._extract_episodes(all_states)
        
        # Analyze persona evolution
        self.persona_states = self._analyze_persona_evolution(all_states)
        
        # Calculate internal metrics
        self.metrics = self._calculate_internal_metrics(all_states)
        
        return {
            "episodes": [self._episode_to_dict(ep) for ep in self.episodes],
            "persona_evolution": [self._persona_to_dict(ps) for ps in self.persona_states],
            "internal_metrics": [self._metrics_to_dict(m) for m in self.metrics],
            "summary_stats": self._generate_summary_stats()
        }
    
    def _extract_episodes(self, states: List[Dict]) -> List[Episode]:
        """Extract episodes based on state changes in events, decisions, and recommendations"""
        episodes = []
        
        for i, state in enumerate(states):
            week_index = state.get('week_index', 1)
            
            # Look for state changes that constitute episodes
            episode_events = []
            
            # 1. New decision chains
            new_decisions = self._find_new_decisions(state, states[i-1] if i > 0 else {})
            episode_events.extend(new_decisions)
            
            # 2. Event state changes (active/completed)
            event_changes = self._find_event_changes(state, states[i-1] if i > 0 else {})
            episode_events.extend(event_changes)
            
            # 3. Significant agent responses/recommendations
            new_responses = self._find_significant_responses(state, states[i-1] if i > 0 else {})
            episode_events.extend(new_responses)
            
            # 4. Member state changes (plan updates, counter changes)
            state_changes = self._find_member_state_changes(state, states[i-1] if i > 0 else {})
            episode_events.extend(state_changes)
            
            # Create episodes from these state changes
            for event in episode_events:
                episode = self._create_episode_from_state_change(event, state, week_index)
                if episode:
                    episodes.append(episode)
        
        return episodes
    
    def _find_new_decisions(self, current_state: Dict, prev_state: Dict) -> List[Dict]:
        """Find new decision chains created in this state"""
        current_decisions = current_state.get('active_decision_chains', [])
        prev_decisions = prev_state.get('active_decision_chains', [])
        
        # Find decision IDs in current that weren't in previous
        prev_ids = {d.get('decision_id') for d in prev_decisions}
        new_decisions = []
        
        for decision in current_decisions:
            if decision.get('decision_id') not in prev_ids:
                new_decisions.append({
                    'type': 'decision_chain',
                    'event': 'new_decision',
                    'data': decision,
                    'title': f"Decision: {decision.get('triggering_event', 'Unknown')}",
                    'description': decision.get('triggering_event', '')
                })
        
        return new_decisions
    
    def _find_event_changes(self, current_state: Dict, prev_state: Dict) -> List[Dict]:
        """Find changes in active/completed events"""
        changes = []
        
        # New active events
        current_active = current_state.get('active_events', [])
        prev_active = prev_state.get('active_events', [])
        prev_active_ids = {e.get('event_id') for e in prev_active}
        
        for event in current_active:
            if event.get('event_id') not in prev_active_ids:
                changes.append({
                    'type': 'event',
                    'event': 'event_started',
                    'data': event,
                    'title': f"Event Started: {event.get('description', 'Unknown')}",
                    'description': event.get('description', '')
                })
        
        # Newly completed events
        current_completed = current_state.get('completed_events', [])
        prev_completed = prev_state.get('completed_events', [])
        prev_completed_ids = {e.get('event_id') for e in prev_completed}
        
        for event in current_completed:
            if event.get('event_id') not in prev_completed_ids:
                changes.append({
                    'type': 'event',
                    'event': 'event_completed',
                    'data': event,
                    'title': f"Event Completed: {event.get('description', 'Unknown')}",
                    'description': event.get('description', '')
                })
        
        return changes
    
    def _find_significant_responses(self, current_state: Dict, prev_state: Dict) -> List[Dict]:
        """Find significant new agent responses with recommendations"""
        current_responses = current_state.get('agent_responses', [])
        prev_responses = prev_state.get('agent_responses', [])
        
        # If more responses in current state, look at new ones
        if len(current_responses) > len(prev_responses):
            new_responses = current_responses[len(prev_responses):]
            significant = []
            
            for response in new_responses:
                # Consider significant if has recommendations, medications, or tests
                if (response.get('recommendations') or 
                    response.get('medications') or 
                    response.get('tests') or
                    response.get('proposed_event')):
                    
                    significant.append({
                        'type': 'agent_response',
                        'event': 'significant_recommendation',
                        'data': response,
                        'title': f"{response.get('agent', 'Agent')} Recommendation",
                        'description': response.get('analysis', response.get('message', ''))[:100]
                    })
            
            return significant
        
        return []
    
    def _find_member_state_changes(self, current_state: Dict, prev_state: Dict) -> List[Dict]:
        """Find significant changes in member state"""
        changes = []
        
        current_member = current_state.get('member_state', {})
        prev_member = prev_state.get('member_state', {})
        
        # Plan updates
        current_plan = current_member.get('plan', {})
        prev_plan = prev_member.get('plan', {})
        
        if current_plan.get('last_update_week', 0) != prev_plan.get('last_update_week', 0):
            changes.append({
                'type': 'member_state',
                'event': 'plan_updated',
                'data': current_plan,
                'title': "Plan Updated",
                'description': f"Member plan updated in week {current_plan.get('last_update_week')}"
            })
        
        # Significant counter changes (like travel)
        current_counters = current_member.get('simulation_counters', {})
        prev_counters = prev_member.get('simulation_counters', {})
        
        # Travel episode (reset to 0)
        if (current_counters.get('weeks_since_last_trip', 0) == 0 and 
            prev_counters.get('weeks_since_last_trip', 0) > 0):
            changes.append({
                'type': 'member_state',
                'event': 'travel_episode',
                'data': current_counters,
                'title': "Travel Episode",
                'description': "Member travel plans discussed"
            })
        
        # Diagnostic test (when weeks_since_last_diagnostic changes significantly)
        current_diag = current_counters.get('weeks_since_last_diagnostic', 0)
        prev_diag = prev_counters.get('weeks_since_last_diagnostic', 0)
        
        if current_diag == 0 and prev_diag > 0:
            changes.append({
                'type': 'member_state', 
                'event': 'diagnostic_scheduled',
                'data': current_counters,
                'title': "Diagnostic Test Scheduled",
                'description': "Diagnostic test scheduled or completed"
            })
        
        return changes
    
    def _create_episode_from_state_change(self, event: Dict, state: Dict, week_index: int) -> Optional[Episode]:
        """Create an episode from a state change event"""
        try:
            # Get relevant chat messages from this week
            chat_history = state.get('chat_history', [])
            relevant_messages = [msg for msg in chat_history 
                               if msg.get('timestamp', '').startswith('2024') or 
                                  msg.get('timestamp', '').startswith('2025')]
            
            # Basic episode info
            episode_id = f"EP_{week_index}_{event['type']}_{len(relevant_messages)}"
            
            # Determine agents involved based on event type
            agents_involved = []
            if event['type'] == 'agent_response':
                agents_involved = [event['data'].get('agent', 'Unknown')]
            elif event['type'] == 'decision_chain':
                analyses = event['data'].get('agent_analyses', [])
                agents_involved = [a.get('agent_name') for a in analyses if a.get('agent_name')]
            else:
                # Look at recent messages for agent involvement
                recent_msgs = relevant_messages[-5:] if relevant_messages else []
                agents_involved = list(set([msg.get('agent', msg.get('role')) 
                                          for msg in recent_msgs 
                                          if msg.get('agent') or msg.get('role') != 'member']))
            
            # Extract recommendations and decision details
            recommendations = self._extract_recommendations_from_event(event)
            decision_id = self._extract_decision_id_from_event(event)
            
            # Create episode with enhanced data
            return Episode(
                episode_id=episode_id,
                title=event['title'],
                start_date=relevant_messages[0]['timestamp'] if relevant_messages else f"2024-12-30T{week_index:02d}:00:00",
                end_date=relevant_messages[-1]['timestamp'] if relevant_messages else f"2024-12-30T{week_index:02d}:00:00",
                duration_days=1,  # Most state changes happen within a day
                week_range=(week_index, week_index),
                trigger_type="system" if event['type'] in ['event', 'member_state'] else "agent",
                trigger_description=event['description'],
                triggered_by=event['data'].get('agent', 'System') if event['type'] == 'agent_response' else 'System',
                messages=relevant_messages[-10:],  # Last 10 messages for context
                agents_involved=agents_involved or ['System'],
                message_count=len(relevant_messages),
                final_outcome=self._determine_outcome_from_event(event),
                outcome_type=self._categorize_outcome_from_event(event),
                friction_points=[],  # Will be populated if needed
                response_time_minutes=None,  # Not applicable for state changes
                time_to_resolution_hours=None,  # Not applicable for state changes  
                agent_switches=len(set(agents_involved)) - 1 if len(agents_involved) > 1 else 0,
                member_satisfaction_indicators=[],
                # Enhanced data
                recommendations=recommendations,
                decision_id=decision_id,
                medications=self._extract_medications_from_event(event),
                tests=self._extract_tests_from_event(event)
            )
            
        except Exception as e:
            print(f"Error creating episode from state change: {e}")
            return None
    
    def _extract_recommendations_from_event(self, event: Dict) -> List[str]:
        """Extract recommendations from event data"""
        recommendations = []
        
        if event['type'] == 'agent_response':
            data = event['data']
            recommendations.extend(data.get('recommendations', []))
        elif event['type'] == 'decision_chain':
            data = event['data']
            for analysis in data.get('agent_analyses', []):
                recommendations.extend(analysis.get('recommendations', []))
        
        return recommendations
    
    def _extract_decision_id_from_event(self, event: Dict) -> Optional[str]:
        """Extract decision ID from event data"""
        if event['type'] == 'decision_chain':
            return event['data'].get('decision_id')
        elif event['type'] == 'agent_response':
            # Check if this response is part of a decision chain
            proposed_event = event['data'].get('proposed_event')
            if proposed_event:
                return proposed_event.get('decision_id')
        return None
    
    def _extract_medications_from_event(self, event: Dict) -> List[str]:
        """Extract medications from event data"""
        medications = []
        
        if event['type'] == 'agent_response':
            data = event['data']
            medications.extend(data.get('medications', []))
        elif event['type'] == 'decision_chain':
            data = event['data']
            for analysis in data.get('agent_analyses', []):
                medications.extend(analysis.get('medications', []))
        
        return medications
    
    def _extract_tests_from_event(self, event: Dict) -> List[str]:
        """Extract tests from event data"""
        tests = []
        
        if event['type'] == 'agent_response':
            data = event['data']
            tests.extend(data.get('tests', []))
        elif event['type'] == 'decision_chain':
            data = event['data']
            for analysis in data.get('agent_analyses', []):
                tests.extend(analysis.get('tests', []))
        
        return tests
    
    def _determine_outcome_from_event(self, event: Dict) -> str:
        """Determine outcome based on event type"""
        event_type = event['type']
        if event_type == 'decision_chain':
            return f"Decision made: {event['data'].get('final_decision', 'Pending')}"
        elif event_type == 'event':
            if event['event'] == 'event_completed':
                return f"Event completed: {event['data'].get('description', '')}"
            else:
                return f"Event started: {event['data'].get('description', '')}"
        elif event_type == 'agent_response':
            return f"Recommendation provided by {event['data'].get('agent', 'Agent')}"
        elif event_type == 'member_state':
            return f"Member state updated: {event['event']}"
        else:
            return "State change recorded"
    
    def _categorize_outcome_from_event(self, event: Dict) -> str:
        """Categorize outcome type based on event"""
        event_type = event['type']
        if event_type == 'decision_chain':
            return "decision_made"
        elif event_type == 'event':
            return "event_transition"
        elif event_type == 'agent_response':
            return "recommendation_provided"
        elif event_type == 'member_state':
            return "state_updated"
        else:
            return "system_change"
    
    def _group_messages_into_threads(self, chat_history: List[Dict]) -> List[List[Dict]]:
        """Group messages into conversation threads based on timing and content"""
        if not chat_history:
            return []
        
        threads = []
        current_thread = []
        
        for i, msg in enumerate(chat_history):
            if i == 0:
                current_thread = [msg]
                continue
            
            # Check if this message starts a new thread
            prev_msg = chat_history[i-1]
            time_gap = self._calculate_time_gap(prev_msg['timestamp'], msg['timestamp'])
            
            # New thread if:
            # 1. Large time gap (>4 hours)
            # 2. Member initiates after END_TURN decision
            # 3. New topic detected (simplified heuristic)
            
            is_new_thread = (
                time_gap > 240 or  # 4 hours in minutes
                (msg['role'] == 'member' and 
                 prev_msg.get('meta', {}).get('decision') == 'END_TURN') or
                self._is_new_topic(current_thread, msg)
            )
            
            if is_new_thread and current_thread:
                threads.append(current_thread)
                current_thread = [msg]
            else:
                current_thread.append(msg)
        
        if current_thread:
            threads.append(current_thread)
        
        return threads
    
    def _create_episode_from_thread(self, messages: List[Dict], week_index: int) -> Optional[Episode]:
        """Create an episode from a message thread"""
        if not messages:
            return None
        
        first_msg = messages[0]
        last_msg = messages[-1]
        
        # Determine trigger
        trigger_type = "member_initiated" if first_msg['role'] == 'member' else "agent_initiated"
        triggered_by = first_msg.get('agent', first_msg['role'])
        
        # Extract agents involved
        agents_involved = list(set([
            msg.get('agent', msg['role']) 
            for msg in messages 
            if msg['role'] != 'member'
        ]))
        
        # Calculate metrics
        response_time = self._calculate_first_response_time(messages)
        resolution_time = self._calculate_resolution_time(messages)
        agent_switches = len(set(agents_involved)) - 1
        
        # Determine outcome
        outcome_type, final_outcome = self._analyze_thread_outcome(messages)
        
        # Detect friction points
        friction_points = self._detect_friction_points(messages)
        
        # Generate episode title
        title = self._generate_episode_title(first_msg, outcome_type)
        
        episode = Episode(
            episode_id=f"EP_{week_index}_{first_msg['msg_id'][:8]}",
            title=title,
            start_date=first_msg['timestamp'],
            end_date=last_msg['timestamp'],
            duration_days=self._calculate_duration_days(first_msg['timestamp'], last_msg['timestamp']),
            week_range=(week_index, week_index),
            
            trigger_type=trigger_type,
            trigger_description=first_msg['text'][:100] + "..." if len(first_msg['text']) > 100 else first_msg['text'],
            triggered_by=triggered_by,
            
            messages=messages,
            agents_involved=agents_involved,
            message_count=len(messages),
            
            final_outcome=final_outcome,
            outcome_type=outcome_type,
            friction_points=friction_points,
            
            response_time_minutes=response_time,
            time_to_resolution_hours=resolution_time,
            agent_switches=agent_switches,
            member_satisfaction_indicators=self._extract_satisfaction_indicators(messages)
        )
        
        return episode
    
    def _analyze_persona_evolution(self, states: List[Dict]) -> List[PersonaState]:
        """Track how member persona evolves over time"""
        persona_states = []
        
        for state in states:
            week_index = state.get('week_index', 1)
            chat_history = state.get('chat_history', [])
            member_state = state.get('member_state', {})
            
            if not chat_history:
                continue
            
            # Analyze member messages for persona indicators
            member_messages = [msg for msg in chat_history if msg['role'] == 'member']
            
            if not member_messages:
                continue
            
            latest_timestamp = member_messages[-1]['timestamp']
            
            # Extract persona characteristics
            engagement_level = self._assess_engagement_level(member_messages)
            health_awareness = self._assess_health_awareness(member_messages)
            communication_style = self._assess_communication_style(member_messages)
            trust_level = self._assess_trust_level(member_messages, chat_history)
            
            # Health status perception
            perceived_health_status = self._extract_health_perception(member_messages)
            primary_concerns = self._extract_primary_concerns(member_messages)
            confidence_in_plan = self._assess_plan_confidence(member_messages)
            
            # Behavioral indicators
            initiative_taking = self._assess_initiative_taking(member_messages)
            data_sharing_willingness = self._assess_data_sharing(member_messages)
            follow_through_likelihood = self._assess_follow_through(member_messages)
            
            persona_state = PersonaState(
                timestamp=latest_timestamp,
                week_index=week_index,
                engagement_level=engagement_level,
                health_awareness=health_awareness,
                communication_style=communication_style,
                trust_level=trust_level,
                perceived_health_status=perceived_health_status,
                primary_concerns=primary_concerns,
                confidence_in_plan=confidence_in_plan,
                initiative_taking=initiative_taking,
                data_sharing_willingness=data_sharing_willingness,
                follow_through_likelihood=follow_through_likelihood
            )
            
            persona_states.append(persona_state)
        
        return persona_states
    
    def _calculate_internal_metrics(self, states: List[Dict]) -> List[InternalMetrics]:
        """Calculate internal operational metrics"""
        metrics = []
        
        for state in states:
            week_index = state.get('week_index', 1)
            chat_history = state.get('chat_history', [])
            agent_responses = state.get('agent_responses', [])
            decision_chains = state.get('active_decision_chains', []) + state.get('completed_decision_chains', [])
            
            # Calculate agent activity
            agent_hours = self._estimate_agent_hours(chat_history, agent_responses)
            consultation_count = self._count_consultations(chat_history)
            response_times = self._calculate_response_times(chat_history)
            
            # Decision quality metrics
            decision_confidence_avg = self._calculate_avg_decision_confidence(decision_chains)
            decision_implementation_rate = self._calculate_implementation_rate(decision_chains)
            decision_revision_count = self._count_decision_revisions(decision_chains)
            
            # Member engagement metrics
            member_messages = [msg for msg in chat_history if msg['role'] == 'member']
            member_initiative_messages = len([msg for msg in member_messages if self._is_initiative_message(msg, chat_history)])
            member_response_rate = self._calculate_member_response_rate(chat_history)
            member_question_complexity = self._assess_question_complexity(member_messages)
            
            week_metrics = InternalMetrics(
                week_index=week_index,
                agent_hours=agent_hours,
                consultation_count=consultation_count,
                response_times=response_times,
                decision_confidence_avg=decision_confidence_avg,
                decision_implementation_rate=decision_implementation_rate,
                decision_revision_count=decision_revision_count,
                member_initiative_messages=member_initiative_messages,
                member_response_rate=member_response_rate,
                member_question_complexity=member_question_complexity
            )
            
            metrics.append(week_metrics)
        
        return metrics
    
    # Helper methods for analysis
    def _calculate_time_gap(self, timestamp1: str, timestamp2: str) -> float:
        """Calculate time gap between timestamps in minutes"""
        try:
            dt1 = datetime.fromisoformat(timestamp1)
            dt2 = datetime.fromisoformat(timestamp2)
            return abs((dt2 - dt1).total_seconds() / 60)
        except:
            return 0
    
    def _is_new_topic(self, current_thread: List[Dict], new_message: Dict) -> bool:
        """Simple heuristic to detect if message introduces new topic"""
        # Look for keywords that indicate new topics
        new_topic_indicators = [
            "i'd like to discuss", "new topic", "changing subject",
            "another question", "different matter", "also wanted to ask",
            "garmin data", "sleep", "travel", "diagnostic test"
        ]
        
        text = new_message['text'].lower()
        return any(indicator in text for indicator in new_topic_indicators)
    
    def _calculate_first_response_time(self, messages: List[Dict]) -> Optional[float]:
        """Calculate time from first message to first response"""
        if len(messages) < 2:
            return None
        
        first_msg = messages[0]
        first_response = next((msg for msg in messages[1:] if msg['role'] != 'member'), None)
        
        if not first_response:
            return None
        
        return self._calculate_time_gap(first_msg['timestamp'], first_response['timestamp'])
    
    def _calculate_resolution_time(self, messages: List[Dict]) -> Optional[float]:
        """Calculate total time to resolution"""
        if len(messages) < 2:
            return None
        
        return self._calculate_time_gap(messages[0]['timestamp'], messages[-1]['timestamp']) / 60  # Convert to hours
    
    def _analyze_thread_outcome(self, messages: List[Dict]) -> Tuple[str, str]:
        """Analyze the outcome of a conversation thread"""
        last_agent_msg = None
        last_member_msg = None
        
        # Find last agent and member messages
        for msg in reversed(messages):
            if msg['role'] != 'member' and not last_agent_msg:
                last_agent_msg = msg
            elif msg['role'] == 'member' and not last_member_msg:
                last_member_msg = msg
            
            if last_agent_msg and last_member_msg:
                break
        
        # Analyze outcome based on content
        if last_agent_msg:
            text = last_agent_msg['text'].lower()
            
            if any(word in text for word in ['attached', 'document', 'plan', 'protocol']):
                return "plan_proposed", "Plan and recommendations provided"
            elif any(word in text for word in ['scheduled', 'appointment', 'call', 'test']):
                return "intervention_scheduled", "Follow-up or intervention scheduled"
            elif any(word in text for word in ['track', 'monitor', 'reassess', 'follow up']):
                return "monitoring_established", "Monitoring and follow-up established"
            else:
                return "information_provided", "Information and guidance provided"
        
        return "incomplete", "Thread incomplete or unclear outcome"
    
    def _detect_friction_points(self, messages: List[Dict]) -> List[str]:
        """Detect potential friction points in the conversation"""
        friction_points = []
        
        # Look for indicators of friction
        for msg in messages:
            text = msg['text'].lower()
            
            if msg['role'] == 'member':
                if any(phrase in text for phrase in ['confused', 'not clear', 'don\'t understand']):
                    friction_points.append("Member confusion detected")
                elif any(phrase in text for phrase in ['concerned', 'worried', 'anxious']):
                    friction_points.append("Member concern/anxiety detected")
                elif "?" in text and text.count("?") > 2:
                    friction_points.append("Multiple member questions - clarity needed")
        
        # Check for long response times
        for i in range(1, len(messages)):
            gap = self._calculate_time_gap(messages[i-1]['timestamp'], messages[i]['timestamp'])
            if gap > 120:  # 2 hours
                friction_points.append(f"Long response delay ({gap:.0f} minutes)")
        
        return list(set(friction_points))  # Remove duplicates
    
    def _generate_episode_title(self, first_msg: Dict, outcome_type: str) -> str:
        """Generate a descriptive title for the episode"""
        text = first_msg['text']
        
        # Extract key topics
        if 'garmin' in text.lower() or 'sleep' in text.lower():
            return "Sleep & Wearable Data Discussion"
        elif 'travel' in text.lower():
            return "Travel Health Planning"
        elif 'diagnostic' in text.lower() or 'test' in text.lower():
            return "Diagnostic Test Scheduling"
        elif 'diet' in text.lower() or 'nutrition' in text.lower():
            return "Nutrition Planning & Guidance"
        elif 'exercise' in text.lower() or 'activity' in text.lower():
            return "Physical Activity Planning"
        elif 'cholesterol' in text.lower() or 'blood pressure' in text.lower():
            return "Cardiovascular Health Management"
        elif outcome_type == "plan_proposed":
            return "Health Plan Development"
        else:
            return "Health Inquiry & Guidance"
    
    # Persona analysis helper methods
    def _assess_engagement_level(self, member_messages: List[Dict]) -> str:
        """Assess member's engagement level"""
        if not member_messages:
            return "low"
        
        avg_length = sum(len(msg['text']) for msg in member_messages) / len(member_messages)
        question_ratio = sum(1 for msg in member_messages if '?' in msg['text']) / len(member_messages)
        
        if avg_length > 100 and question_ratio > 0.3:
            return "high"
        elif avg_length > 50 or question_ratio > 0.2:
            return "medium"
        else:
            return "low"
    
    def _assess_health_awareness(self, member_messages: List[Dict]) -> str:
        """Assess member's health awareness level"""
        proactive_indicators = ['prevent', 'optimize', 'track', 'monitor', 'improve']
        reactive_indicators = ['problem', 'concerned', 'issue', 'worried']
        
        text = ' '.join(msg['text'].lower() for msg in member_messages)
        
        proactive_count = sum(1 for indicator in proactive_indicators if indicator in text)
        reactive_count = sum(1 for indicator in reactive_indicators if indicator in text)
        
        if proactive_count > reactive_count:
            return "proactive"
        elif reactive_count > 0:
            return "reactive"
        else:
            return "passive"
    
    # Add more helper methods as needed...
    def _assess_communication_style(self, member_messages: List[Dict]) -> str:
        avg_length = sum(len(msg['text']) for msg in member_messages) / len(member_messages)
        return "detailed" if avg_length > 80 else "brief"
    
    def _assess_trust_level(self, member_messages: List[Dict], all_messages: List[Dict]) -> str:
        # Simple heuristic - look for positive feedback and follow-through
        positive_indicators = ['thank you', 'appreciate', 'helpful', 'great']
        text = ' '.join(msg['text'].lower() for msg in member_messages)
        
        if any(indicator in text for indicator in positive_indicators):
            return "high"
        elif len(member_messages) > 3:  # Continued engagement indicates building trust
            return "building"
        else:
            return "skeptical"
    
    def _extract_health_perception(self, member_messages: List[Dict]) -> str:
        return "concerned"  # Simplified for now
    
    def _extract_primary_concerns(self, member_messages: List[Dict]) -> List[str]:
        concerns = []
        text = ' '.join(msg['text'].lower() for msg in member_messages)
        
        if 'heart' in text or 'cholesterol' in text:
            concerns.append("cardiovascular health")
        if 'sleep' in text:
            concerns.append("sleep quality")
        if 'stress' in text:
            concerns.append("stress management")
        
        return concerns
    
    def _assess_plan_confidence(self, member_messages: List[Dict]) -> float:
        return 0.8  # Simplified for now
    
    def _assess_initiative_taking(self, member_messages: List[Dict]) -> bool:
        return len(member_messages) > 2
    
    def _assess_data_sharing(self, member_messages: List[Dict]) -> str:
        return "open"  # Simplified for now
    
    def _assess_follow_through(self, member_messages: List[Dict]) -> float:
        return 0.85  # Simplified for now
    
    # Internal metrics helper methods
    def _estimate_agent_hours(self, chat_history: List[Dict], agent_responses: List[Dict]) -> Dict[str, float]:
        """Estimate hours spent by each agent based on detailed activity analysis"""
        agent_hours = {}
        agent_activities = {}
        
        # Analyze from agent responses (more detailed data)
        for response in agent_responses:
            agent = response.get('agent', 'Unknown')
            
            # Estimate time based on response complexity and activities
            message_length = len(response.get('message', ''))
            recommendations_count = len(response.get('recommendations', []))
            medications_count = len(response.get('medications', []))
            tests_count = len(response.get('tests', []))
            
            # Base time: 8 minutes per response + extra for complexity
            base_time = 8  # minutes
            
            # Complexity factors
            complexity_time = (message_length / 100) * 3  # 3 min per 100 chars
            recommendation_time = recommendations_count * 6  # 6 min per recommendation
            medication_time = medications_count * 12  # 12 min per medication review
            test_time = tests_count * 10  # 10 min per test analysis
            
            # Analysis complexity
            analysis_length = len(response.get('analysis', ''))
            analysis_time = (analysis_length / 200) * 4  # 4 min per 200 chars of analysis
            
            # Expert routing time
            if response.get('needs_expert') == 'true':
                expert_time = 8  # 8 min for coordination
            else:
                expert_time = 0
            
            total_minutes = (base_time + complexity_time + recommendation_time + 
                           medication_time + test_time + analysis_time + expert_time)
            total_hours = total_minutes / 60
            
            agent_hours[agent] = agent_hours.get(agent, 0) + total_hours
            
            # Track activities for detailed metrics
            if agent not in agent_activities:
                agent_activities[agent] = {
                    'messages': 0, 'recommendations': 0, 'medications': 0, 
                    'tests': 0, 'expert_consultations': 0, 'analysis_time': 0
                }
            
            agent_activities[agent]['messages'] += 1
            agent_activities[agent]['recommendations'] += recommendations_count
            agent_activities[agent]['medications'] += medications_count
            agent_activities[agent]['tests'] += tests_count
            agent_activities[agent]['analysis_time'] += analysis_time
            if response.get('needs_expert') == 'true':
                agent_activities[agent]['expert_consultations'] += 1
        
        # Fallback to chat history if no agent responses
        if not agent_responses:
            for msg in chat_history:
                if msg['role'] != 'member':
                    agent = msg.get('agent', msg['role'])
                    # Estimate 5-10 minutes per response
                    estimated_minutes = max(5, min(10, len(msg['text']) / 20))
                    agent_hours[agent] = agent_hours.get(agent, 0) + estimated_minutes / 60
        
        # Store activities for potential future use
        self.agent_activities = getattr(self, 'agent_activities', {})
        self.agent_activities.update(agent_activities)
        
        return agent_hours
    
    def _count_consultations(self, chat_history: List[Dict]) -> Dict[str, int]:
        """Count consultations by agent"""
        consultation_count = {}
        
        for msg in chat_history:
            if msg['role'] != 'member':
                agent = msg.get('agent', msg['role'])
                consultation_count[agent] = consultation_count.get(agent, 0) + 1
        
        return consultation_count
    
    def _calculate_response_times(self, chat_history: List[Dict]) -> Dict[str, List[float]]:
        """Calculate response times for each agent"""
        response_times = {}
        
        for i in range(1, len(chat_history)):
            current_msg = chat_history[i]
            prev_msg = chat_history[i-1]
            
            if prev_msg['role'] == 'member' and current_msg['role'] != 'member':
                agent = current_msg.get('agent', current_msg['role'])
                response_time = self._calculate_time_gap(prev_msg['timestamp'], current_msg['timestamp'])
                
                if agent not in response_times:
                    response_times[agent] = []
                response_times[agent].append(response_time)
        
        return response_times
    
    def _calculate_avg_decision_confidence(self, decision_chains: List[Dict]) -> float:
        """Calculate average decision confidence"""
        if not decision_chains:
            return 0.0
        
        total_confidence = 0
        count = 0
        
        for chain in decision_chains:
            for analysis in chain.get('agent_analyses', []):
                total_confidence += analysis.get('confidence_level', 0)
                count += 1
        
        return total_confidence / count if count > 0 else 0.0
    
    def _calculate_implementation_rate(self, decision_chains: List[Dict]) -> float:
        """Calculate decision implementation rate"""
        if not decision_chains:
            return 0.0
        
        implemented = sum(1 for chain in decision_chains 
                         if chain.get('implementation_status') == 'completed')
        
        return implemented / len(decision_chains)
    
    def _count_decision_revisions(self, decision_chains: List[Dict]) -> int:
        """Count decision revisions"""
        return 0  # Simplified for now
    
    def _is_initiative_message(self, msg: Dict, chat_history: List[Dict]) -> bool:
        """Check if message is member-initiated"""
        # Find previous message
        msg_index = next((i for i, m in enumerate(chat_history) if m['msg_id'] == msg['msg_id']), -1)
        
        if msg_index <= 0:
            return True  # First message is always initiative
        
        prev_msg = chat_history[msg_index - 1]
        
        # Initiative if previous message was END_TURN or large time gap
        return (prev_msg.get('meta', {}).get('decision') == 'END_TURN' or
                self._calculate_time_gap(prev_msg['timestamp'], msg['timestamp']) > 240)
    
    def _calculate_member_response_rate(self, chat_history: List[Dict]) -> float:
        """Calculate member response rate to agent messages"""
        agent_messages = [msg for msg in chat_history if msg['role'] != 'member']
        member_responses = 0
        
        for i, msg in enumerate(chat_history):
            if msg['role'] != 'member' and i < len(chat_history) - 1:
                next_msg = chat_history[i + 1]
                if next_msg['role'] == 'member':
                    member_responses += 1
        
        return member_responses / len(agent_messages) if agent_messages else 0.0
    
    def _assess_question_complexity(self, member_messages: List[Dict]) -> float:
        """Assess complexity of member questions (1.0 to 5.0)"""
        if not member_messages:
            return 1.0
        
        complexity_indicators = ['why', 'how', 'what if', 'explain', 'detailed', 'specific']
        total_complexity = 0
        
        for msg in member_messages:
            text = msg['text'].lower()
            complexity = 1.0
            
            # Base complexity on length and question words
            if len(text) > 100:
                complexity += 1.0
            if '?' in text:
                complexity += 0.5 * text.count('?')
            
            # Add complexity for specific indicators
            for indicator in complexity_indicators:
                if indicator in text:
                    complexity += 0.5
            
            total_complexity += min(5.0, complexity)
        
        return total_complexity / len(member_messages)
    
    def _calculate_duration_days(self, start_timestamp: str, end_timestamp: str) -> int:
        """Calculate duration in days between timestamps"""
        try:
            start = datetime.fromisoformat(start_timestamp)
            end = datetime.fromisoformat(end_timestamp)
            return max(1, (end - start).days)
        except:
            return 1
    
    def _extract_satisfaction_indicators(self, messages: List[Dict]) -> List[str]:
        """Extract member satisfaction indicators"""
        indicators = []
        
        for msg in messages:
            if msg['role'] == 'member':
                text = msg['text'].lower()
                
                if any(word in text for word in ['thank', 'appreciate', 'helpful']):
                    indicators.append("positive_feedback")
                elif any(word in text for word in ['great', 'excellent', 'perfect']):
                    indicators.append("enthusiastic_response")
                elif 'looking forward' in text:
                    indicators.append("future_engagement")
        
        return indicators
    
    def _generate_summary_stats(self) -> Dict[str, Any]:
        """Generate summary statistics"""
        return {
            "total_episodes": len(self.episodes),
            "avg_episode_duration_hours": np.mean([ep.time_to_resolution_hours for ep in self.episodes if ep.time_to_resolution_hours]),
            "avg_response_time_minutes": np.mean([ep.response_time_minutes for ep in self.episodes if ep.response_time_minutes]),
            "member_initiated_episodes": len([ep for ep in self.episodes if ep.trigger_type == "member_initiated"]),
            "total_friction_points": sum(len(ep.friction_points) for ep in self.episodes),
            "persona_evolution_points": len(self.persona_states)
        }
    
    # Conversion methods for output
    def _episode_to_dict(self, episode: Episode) -> Dict[str, Any]:
        """Convert Episode to dictionary"""
        return {
            "episode_id": episode.episode_id,
            "title": episode.title,
            "start_date": episode.start_date,
            "end_date": episode.end_date,
            "duration_days": episode.duration_days,
            "week_range": episode.week_range,
            "trigger_type": episode.trigger_type,
            "trigger_description": episode.trigger_description,
            "triggered_by": episode.triggered_by,
            "messages": episode.messages,  # Include messages
            "agents_involved": episode.agents_involved,
            "message_count": episode.message_count,
            "final_outcome": episode.final_outcome,
            "outcome_type": episode.outcome_type,
            "friction_points": episode.friction_points,
            "response_time_minutes": episode.response_time_minutes,
            "time_to_resolution_hours": episode.time_to_resolution_hours,
            "agent_switches": episode.agent_switches,
            "member_satisfaction_indicators": episode.member_satisfaction_indicators,
            # Enhanced fields
            "recommendations": episode.recommendations or [],
            "decision_id": episode.decision_id,
            "medications": episode.medications or [],
            "tests": episode.tests or []
        }
    
    def _persona_to_dict(self, persona: PersonaState) -> Dict[str, Any]:
        """Convert PersonaState to dictionary"""
        return {
            "timestamp": persona.timestamp,
            "week_index": persona.week_index,
            "engagement_level": persona.engagement_level,
            "health_awareness": persona.health_awareness,
            "communication_style": persona.communication_style,
            "trust_level": persona.trust_level,
            "perceived_health_status": persona.perceived_health_status,
            "primary_concerns": persona.primary_concerns,
            "confidence_in_plan": persona.confidence_in_plan,
            "initiative_taking": persona.initiative_taking,
            "data_sharing_willingness": persona.data_sharing_willingness,
            "follow_through_likelihood": persona.follow_through_likelihood
        }
    
    def _metrics_to_dict(self, metrics: InternalMetrics) -> Dict[str, Any]:
        """Convert InternalMetrics to dictionary"""
        return {
            "week_index": metrics.week_index,
            "agent_hours": metrics.agent_hours,
            "consultation_count": metrics.consultation_count,
            "response_times": {k: {"avg": np.mean(v), "count": len(v)} for k, v in metrics.response_times.items()},
            "decision_confidence_avg": metrics.decision_confidence_avg,
            "decision_implementation_rate": metrics.decision_implementation_rate,
            "decision_revision_count": metrics.decision_revision_count,
            "member_initiative_messages": metrics.member_initiative_messages,
            "member_response_rate": metrics.member_response_rate,
            "member_question_complexity": metrics.member_question_complexity
        }
