#!/usr/bin/env python3
"""
Enhanced Member Journey Dashboard
With recommendations, decision backtracking, and detailed agent time tracking
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
import json
import glob
from datetime import datetime
from journey_analyzer import JourneyAnalyzer
import networkx as nx

class EnhancedDashboard:
    """Enhanced dashboard with recommendations and decision tracking"""
    
    def __init__(self):
        self.journey_analyzer = JourneyAnalyzer()
        
        # Initialize session state
        if 'journey_data' not in st.session_state:
            st.session_state.journey_data = None
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
    
    def run(self):
        """Main dashboard application"""
        st.set_page_config(
            page_title="Enhanced Journey Dashboard",
            page_icon="🏥",
            layout="wide"
        )
        
        st.title("🏥 Enhanced Member Journey Dashboard")
        st.markdown("Complete visualization with recommendations, decisions, and agent analytics")
        
        # Sidebar for data loading and navigation
        self._render_sidebar()
        
        # Main content
        if st.session_state.data_loaded and st.session_state.journey_data:
            self._render_dashboard()
        else:
            self._render_welcome()
    
    def _render_sidebar(self):
        """Enhanced sidebar with navigation"""
        st.sidebar.header("🔧 Controls")
        
        # Data loading
        checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
        
        if checkpoint_files:
            st.sidebar.success(f"Found {len(checkpoint_files)} files")
            
            if st.sidebar.button("🔄 Load All Data"):
                with st.spinner("Analyzing journey data..."):
                    journey_data = self.journey_analyzer.analyze_journey(checkpoint_files)
                    st.session_state.journey_data = journey_data
                    st.session_state.data_loaded = True
                st.sidebar.success("✅ Data loaded!")
                st.rerun()
        else:
            st.sidebar.warning("No checkpoint files found")
        
        # Navigation
        if st.session_state.data_loaded:
            st.sidebar.subheader("📊 Views")
            view = st.sidebar.selectbox(
                "Select View",
                ["Overview", "Episodes & Recommendations", "Decision Backtracking", "Agent Time Analysis", "Detailed Insights"]
            )
            st.session_state['current_view'] = view
    
    def _render_welcome(self):
        """Welcome screen"""
        st.markdown("""
        ## 🎯 Enhanced Journey Dashboard Features
        
        ### 📋 **Episodes & Recommendations**
        - State-change based episodes (not just conversations)
        - Actual recommendations provided by agents
        - Medications and tests prescribed
        - Decision IDs for full traceability
        
        ### 🔄 **Decision Backtracking**
        - Visual decision trees using decision IDs
        - Agent collaboration flows
        - Evidence and reasoning chains
        - Decision outcome tracking
        
        ### ⏱️ **Agent Time Analysis**
        - Detailed time estimation based on activities
        - Breakdown by recommendations, analysis, coordination
        - Agent efficiency metrics
        - Activity complexity scoring
        
        Use the sidebar to load your data and explore these features.
        """)
    
    def _render_dashboard(self):
        """Main dashboard based on selected view"""
        data = st.session_state.journey_data
        view = st.session_state.get('current_view', 'Overview')
        
        if view == "Overview":
            self._render_overview(data)
        elif view == "Episodes & Recommendations":
            self._render_episodes_recommendations(data)
        elif view == "Decision Backtracking":
            self._render_decision_backtracking(data)
        elif view == "Agent Time Analysis":
            self._render_agent_time_analysis(data)
        elif view == "Detailed Insights":
            self._render_detailed_insights(data)
    
    def _render_overview(self, data):
        """Enhanced overview with key metrics"""
        st.header("📊 Journey Overview")
        
        episodes = data.get('episodes', [])
        metrics = data.get('internal_metrics', [])
        summary = data.get('summary_stats', {})
        
        # Key metrics row
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Episodes", len(episodes))
        
        with col2:
            total_recommendations = sum(len(ep.get('recommendations', [])) for ep in episodes)
            st.metric("Recommendations", total_recommendations)
        
        with col3:
            episodes_with_decisions = sum(1 for ep in episodes if ep.get('decision_id'))
            st.metric("Decision Episodes", episodes_with_decisions)
        
        with col4:
            if metrics:
                total_agent_hours = sum(
                    sum(week.get('agent_hours', {}).values()) 
                    for week in metrics
                )
                st.metric("Total Agent Hours", f"{total_agent_hours:.1f}h")
            else:
                st.metric("Total Agent Hours", "N/A")
        
        with col5:
            unique_agents = set()
            for ep in episodes:
                unique_agents.update(ep.get('agents_involved', []))
            st.metric("Active Agents", len(unique_agents))
        
        # Episode types distribution
        st.subheader("📈 Episode Distribution")
        
        col1, col2 = st.columns(2)
        
        with col1:
            episode_types = [ep.get('outcome_type', 'unknown') for ep in episodes]
            type_counts = pd.Series(episode_types).value_counts()
            
            fig = px.pie(
                values=type_counts.values,
                names=type_counts.index,
                title="Episodes by Outcome Type"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            trigger_types = [ep.get('trigger_type', 'unknown') for ep in episodes]
            trigger_counts = pd.Series(trigger_types).value_counts()
            
            fig = px.pie(
                values=trigger_counts.values,
                names=trigger_counts.index,
                title="Episodes by Trigger Type"
            )
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_episodes_recommendations(self, data):
        """Episodes with detailed recommendations"""
        st.header("📋 Episodes & Recommendations")
        
        episodes = data.get('episodes', [])
        
        if not episodes:
            st.warning("No episodes found")
            return
        
        # Episode selector
        episode_titles = [f"{ep['title']} (Week {ep['week_range'][0]})" for ep in episodes]
        selected_idx = st.selectbox("Select Episode:", range(len(episode_titles)), format_func=lambda x: episode_titles[x])
        
        if selected_idx is not None:
            episode = episodes[selected_idx]
            
            # Episode header
            st.subheader(f"📖 {episode['title']}")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.write(f"**Week:** {episode['week_range'][0]}-{episode['week_range'][1]}")
                st.write(f"**Triggered by:** {episode['triggered_by']}")
                st.write(f"**Type:** {episode['outcome_type']}")
            
            with col2:
                st.write(f"**Agents:** {', '.join(episode['agents_involved'])}")
                st.write(f"**Duration:** {episode['duration_days']} days")
                if episode.get('decision_id'):
                    st.write(f"**Decision ID:** `{episode['decision_id']}`")
            
            with col3:
                st.write(f"**Messages:** {episode['message_count']}")
                st.write(f"**Agent Switches:** {episode['agent_switches']}")
                st.write(f"**Outcome:** {episode['outcome_type']}")
            
            # Recommendations section
            if episode.get('recommendations'):
                st.subheader("💡 Recommendations Provided")
                for i, rec in enumerate(episode['recommendations'], 1):
                    st.write(f"{i}. {rec}")
            
            # Medications section
            if episode.get('medications'):
                st.subheader("💊 Medications")
                for med in episode['medications']:
                    st.write(f"• {med}")
            
            # Tests section
            if episode.get('tests'):
                st.subheader("🔬 Tests")
                for test in episode['tests']:
                    st.write(f"• {test}")
            
            # Episode outcome
            st.subheader("🎯 Outcome")
            st.write(episode['final_outcome'])
            
            # Friction points
            if episode.get('friction_points'):
                st.subheader("⚠️ Friction Points")
                for fp in episode['friction_points']:
                    st.write(f"• {fp}")
    
    def _render_decision_backtracking(self, data):
        """Decision backtracking visualization"""
        st.header("🔄 Decision Backtracking")
        
        # Load all decision chains from checkpoints
        checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
        all_decisions = []
        decision_episodes = {}
        
        for file_path in checkpoint_files:
            try:
                with open(file_path, 'r') as f:
                    checkpoint = json.load(f)
                    state = checkpoint['state']
                    
                    # Get all decision chains
                    active_decisions = state.get('active_decision_chains', [])
                    completed_decisions = state.get('completed_decision_chains', [])
                    all_decisions.extend(active_decisions + completed_decisions)
                    
            except Exception as e:
                st.warning(f"Could not load {file_path}: {e}")
        
        # Link decisions to episodes
        episodes = data.get('episodes', [])
        for episode in episodes:
            if episode.get('decision_id'):
                decision_episodes[episode['decision_id']] = episode
        
        if not all_decisions:
            st.warning("No decision chains found")
            return
        
        # Decision selector
        decision_options = {}
        for decision in all_decisions:
            decision_id = decision.get('decision_id', 'Unknown')
            trigger = decision.get('triggering_event', 'Unknown trigger')
            decision_options[f"{decision_id}: {trigger[:50]}..."] = decision
        
        selected_key = st.selectbox("Select Decision to Analyze:", list(decision_options.keys()))
        
        if selected_key:
            decision = decision_options[selected_key]
            decision_id = decision.get('decision_id')
            
            # Decision overview
            st.subheader(f"🔍 Decision: {decision_id}")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Trigger:** {decision.get('triggering_event', 'N/A')}")
                st.write(f"**Priority:** {decision.get('priority', 'N/A')}")
                st.write(f"**Status:** {decision.get('status', 'N/A')}")
            
            with col2:
                st.write(f"**Week:** {decision.get('week_index', 'N/A')}")
                st.write(f"**Member:** {decision.get('member_id', 'N/A')}")
                st.write(f"**Decision Maker:** {decision.get('decision_maker', 'N/A')}")
            
            # Agent analyses
            analyses = decision.get('agent_analyses', [])
            if analyses:
                st.subheader("👥 Agent Analyses")
                
                for analysis in analyses:
                    with st.expander(f"{analysis.get('agent_name', 'Unknown Agent')} - {analysis.get('analysis_type', 'Analysis')}"):
                        st.write(f"**Confidence:** {analysis.get('confidence_level', 0):.0%}")
                        
                        if analysis.get('key_findings'):
                            st.write("**Key Findings:**")
                            for finding in analysis['key_findings']:
                                st.write(f"• {finding}")
                        
                        if analysis.get('recommendations'):
                            st.write("**Recommendations:**")
                            for rec in analysis['recommendations']:
                                st.write(f"• {rec}")
                        
                        if analysis.get('concerns'):
                            st.write("**Concerns:**")
                            for concern in analysis['concerns']:
                                st.write(f"• {concern}")
            
            # Final decision
            if decision.get('final_decision'):
                st.subheader("⚖️ Final Decision")
                st.write(decision['final_decision'])
                
                if decision.get('decision_rationale'):
                    st.write("**Rationale:**")
                    st.write(decision['decision_rationale'])
            
            # Linked episode
            if decision_id in decision_episodes:
                episode = decision_episodes[decision_id]
                st.subheader("🔗 Related Episode")
                st.write(f"**Episode:** {episode['title']}")
                st.write(f"**Outcome:** {episode['final_outcome']}")
    
    def _render_agent_time_analysis(self, data):
        """Detailed agent time analysis"""
        st.header("⏱️ Agent Time Analysis")
        
        metrics = data.get('internal_metrics', [])
        episodes = data.get('episodes', [])
        
        if not metrics:
            st.warning("No time metrics available")
            return
        
        # Aggregate agent hours across all weeks
        total_agent_hours = {}
        total_activities = {}
        
        for week_metrics in metrics:
            agent_hours = week_metrics.get('agent_hours', {})
            for agent, hours in agent_hours.items():
                total_agent_hours[agent] = total_agent_hours.get(agent, 0) + hours
        
        # Time breakdown visualization
        if total_agent_hours:
            st.subheader("📊 Total Time by Agent")
            
            agents = list(total_agent_hours.keys())
            hours = list(total_agent_hours.values())
            
            fig = px.bar(
                x=agents,
                y=hours,
                title="Total Hours Spent by Each Agent",
                labels={'x': 'Agent', 'y': 'Hours'},
                color=hours,
                color_continuous_scale='Blues'
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Weekly time trends
        st.subheader("📈 Weekly Time Trends")
        
        weekly_data = []
        for week_metrics in metrics:
            week = week_metrics.get('week_index', 0)
            agent_hours = week_metrics.get('agent_hours', {})
            
            for agent, hours in agent_hours.items():
                weekly_data.append({
                    'Week': week,
                    'Agent': agent,
                    'Hours': hours
                })
        
        if weekly_data:
            df = pd.DataFrame(weekly_data)
            
            fig = px.line(
                df,
                x='Week',
                y='Hours',
                color='Agent',
                title="Agent Time Trends Over Weeks",
                markers=True
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Activity breakdown
        st.subheader("🎯 Activity Breakdown")
        
        # Calculate activity-based metrics from episodes
        agent_activities = {}
        for episode in episodes:
            for agent in episode.get('agents_involved', []):
                if agent not in agent_activities:
                    agent_activities[agent] = {
                        'episodes': 0,
                        'recommendations': 0,
                        'medications': 0,
                        'tests': 0
                    }
                
                agent_activities[agent]['episodes'] += 1
                agent_activities[agent]['recommendations'] += len(episode.get('recommendations', []))
                agent_activities[agent]['medications'] += len(episode.get('medications', []))
                agent_activities[agent]['tests'] += len(episode.get('tests', []))
        
        # Display activity breakdown
        for agent, activities in agent_activities.items():
            with st.expander(f"👨‍⚕️ {agent} Activities"):
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Episodes", activities['episodes'])
                with col2:
                    st.metric("Recommendations", activities['recommendations'])
                with col3:
                    st.metric("Medications", activities['medications'])
                with col4:
                    st.metric("Tests", activities['tests'])
                
                # Efficiency calculation
                total_hours = total_agent_hours.get(agent, 1)
                recommendations_per_hour = activities['recommendations'] / total_hours
                st.write(f"**Efficiency:** {recommendations_per_hour:.2f} recommendations/hour")
    
    def _render_detailed_insights(self, data):
        """Detailed insights and correlations"""
        st.header("🔬 Detailed Insights")
        
        episodes = data.get('episodes', [])
        metrics = data.get('internal_metrics', [])
        
        # Decision effectiveness
        st.subheader("📊 Decision Effectiveness")
        
        decision_episodes = [ep for ep in episodes if ep.get('decision_id')]
        
        if decision_episodes:
            effectiveness_data = []
            for ep in decision_episodes:
                effectiveness_data.append({
                    'Episode': ep['title'][:30],
                    'Agents': len(ep['agents_involved']),
                    'Recommendations': len(ep.get('recommendations', [])),
                    'Week': ep['week_range'][0],
                    'Outcome': ep['outcome_type']
                })
            
            df = pd.DataFrame(effectiveness_data)
            
            fig = px.scatter(
                df,
                x='Agents',
                y='Recommendations',
                size='Week',
                color='Outcome',
                hover_data=['Episode'],
                title="Decision Complexity vs Recommendations"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        # Recommendation patterns
        st.subheader("💡 Recommendation Patterns")
        
        all_recommendations = []
        for ep in episodes:
            all_recommendations.extend(ep.get('recommendations', []))
        
        if all_recommendations:
            # Simple word frequency for recommendations
            word_freq = {}
            for rec in all_recommendations:
                words = rec.lower().split()
                for word in words:
                    if len(word) > 3:  # Skip short words
                        word_freq[word] = word_freq.get(word, 0) + 1
            
            # Top recommendation keywords
            top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:10]
            
            if top_words:
                words, counts = zip(*top_words)
                
                fig = px.bar(
                    x=list(counts),
                    y=list(words),
                    orientation='h',
                    title="Most Common Recommendation Keywords"
                )
                st.plotly_chart(fig, use_container_width=True)
        
        # Summary statistics
        st.subheader("📈 Summary Statistics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Episode Statistics:**")
            st.write(f"• Total episodes: {len(episodes)}")
            st.write(f"• Episodes with recommendations: {sum(1 for ep in episodes if ep.get('recommendations'))}")
            st.write(f"• Episodes with medications: {sum(1 for ep in episodes if ep.get('medications'))}")
            st.write(f"• Episodes with tests: {sum(1 for ep in episodes if ep.get('tests'))}")
        
        with col2:
            st.write("**Agent Statistics:**")
            if metrics:
                avg_weekly_hours = sum(
                    sum(week.get('agent_hours', {}).values()) 
                    for week in metrics
                ) / len(metrics) if metrics else 0
                st.write(f"• Average weekly agent hours: {avg_weekly_hours:.1f}")
            
            unique_agents = set()
            for ep in episodes:
                unique_agents.update(ep.get('agents_involved', []))
            st.write(f"• Unique agents involved: {len(unique_agents)}")

def main():
    """Main application entry point"""
    dashboard = EnhancedDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
