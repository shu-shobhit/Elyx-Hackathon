#!/usr/bin/env python3
"""
Advanced Member Journey Visualization Dashboard
Comprehensive Streamlit app with episode tracking, persona analysis, and decision traceability
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
import glob
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any, Optional
import uuid

# Import our analysis components
from journey_analyzer import JourneyAnalyzer, Episode, PersonaState, InternalMetrics
from decision_visualizer import DecisionVisualizer
from state import ConversationalState

class AdvancedDashboard:
    """Advanced dashboard for member journey visualization"""
    
    def __init__(self):
        self.journey_analyzer = JourneyAnalyzer()
        self.decision_visualizer = DecisionVisualizer()
        
        # Initialize session state
        if 'journey_data' not in st.session_state:
            st.session_state.journey_data = None
        if 'data_loaded' not in st.session_state:
            st.session_state.data_loaded = False
            
        self.journey_data = st.session_state.journey_data
        
    def run(self):
        """Main dashboard application"""
        st.set_page_config(
            page_title="Elyx Member Journey Dashboard",
            page_icon="🏥",
            layout="wide"
        )
        
        st.title("🏥 Elyx Member Journey Dashboard")
        st.markdown("Comprehensive visualization of member health journey, decisions, and outcomes")
        
        # Sidebar for data loading and controls
        self._render_sidebar()
        
        # Main content area
        if st.session_state.data_loaded and st.session_state.journey_data:
            self.journey_data = st.session_state.journey_data
            self._render_main_dashboard()
        else:
            self._render_welcome_screen()
    
    def _render_sidebar(self):
        """Render sidebar with controls and data loading"""
        st.sidebar.header("📊 Data Controls")
        
        # Data loading section
        st.sidebar.subheader("Load Journey Data")
        
        # Auto-detect checkpoint files
        checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
        
        if checkpoint_files:
            st.sidebar.success(f"Found {len(checkpoint_files)} checkpoint files")
            
            if st.sidebar.button("🔄 Load All Data"):
                with st.spinner("Analyzing journey data..."):
                    journey_data = self.journey_analyzer.analyze_journey(checkpoint_files)
                    # Store in session state
                    st.session_state.journey_data = journey_data
                    st.session_state.data_loaded = True
                    self.journey_data = journey_data
                st.sidebar.success("✅ Data loaded successfully!")
                st.rerun()
        else:
            st.sidebar.warning("No checkpoint files found in 'checkpoints/' directory")
            
            # Manual file upload option
            uploaded_files = st.sidebar.file_uploader(
                "Upload checkpoint JSON files",
                accept_multiple_files=True,
                type=['json']
            )
            
            if uploaded_files and st.sidebar.button("Process Uploaded Files"):
                # Save uploaded files temporarily and process
                temp_files = []
                for uploaded_file in uploaded_files:
                    temp_path = f"temp_{uploaded_file.name}"
                    with open(temp_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    temp_files.append(temp_path)
                
                with st.spinner("Processing uploaded data..."):
                    self.journey_data = self.journey_analyzer.analyze_journey(temp_files)
                
                # Clean up temp files
                import os
                for temp_file in temp_files:
                    os.remove(temp_file)
                
                st.sidebar.success("✅ Uploaded data processed!")
                st.rerun()
        
        # Dashboard controls
        if st.session_state.data_loaded and st.session_state.journey_data:
            st.sidebar.subheader("📈 Dashboard Controls")
            
            # Time range filter
            episodes = st.session_state.journey_data.get('episodes', [])
            if episodes:
                min_week = min(ep['week_range'][0] for ep in episodes)
                max_week = max(ep['week_range'][1] for ep in episodes)
                
                week_range = st.sidebar.slider(
                    "Week Range",
                    min_value=min_week,
                    max_value=max_week,
                    value=(min_week, max_week)
                )
                st.session_state['week_range'] = week_range
            
            # View mode selection
            view_mode = st.sidebar.selectbox(
                "Dashboard View",
                ["Overview", "Episode Analysis", "Persona Evolution", "Decision Traceback", "Internal Metrics", "Comparative Analysis"]
            )
            st.session_state['view_mode'] = view_mode
    
    def _render_welcome_screen(self):
        """Render welcome screen when no data is loaded"""
        st.markdown("""
        ## 👋 Welcome to the Elyx Member Journey Dashboard
        
        This dashboard provides comprehensive insights into member health journeys, including:
        
        ### 📋 **Episode Analysis**
        - Track distinct health episodes with triggers, outcomes, and friction points
        - Analyze response times and resolution efficiency
        - Identify patterns in member-initiated vs agent-initiated interactions
        
        ### 👤 **Persona Evolution**
        - Monitor how member personas change over time
        - Track engagement levels, health awareness, and trust building
        - Understand communication preferences and behavioral patterns
        
        ### 🔍 **Decision Traceability**
        - Visualize complete decision trees with evidence and reasoning
        - Track agent collaboration and confidence levels
        - Understand why specific treatments/interventions were recommended
        
        ### 📊 **Internal Metrics**
        - Monitor consultant hours and response times
        - Track decision quality and implementation rates
        - Analyze member engagement and satisfaction indicators
        
        ---
        
        **Get Started:** Use the sidebar to load your checkpoint data files.
        """)
        
        # Show sample visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Sample Episode Timeline")
            sample_episodes_df = pd.DataFrame([
                {"Episode": "Initial Onboarding", "Start": "2024-01-01", "Duration": 3, "Outcome": "Plan Proposed"},
                {"Episode": "Sleep Data Review", "Start": "2024-01-05", "Duration": 1, "Outcome": "Protocol Implemented"},
                {"Episode": "Travel Planning", "Start": "2024-01-12", "Duration": 2, "Outcome": "Guidance Provided"},
            ])
            
            fig = px.timeline(
                sample_episodes_df,
                x_start="Start",
                x_end="Start",  # Will be calculated
                y="Episode",
                color="Outcome",
                title="Member Episode Timeline (Sample)"
            )
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            st.subheader("🧠 Sample Decision Tree")
            # Create sample decision tree
            sample_tree = go.Figure()
            sample_tree.add_trace(go.Scatter(
                x=[0, 1, 2, 1, 2],
                y=[2, 3, 3, 1, 1],
                mode='markers+text',
                text=['Trigger', 'Evidence', 'Analysis', 'Risk', 'Decision'],
                textposition="middle center",
                marker=dict(size=[30, 25, 25, 25, 35], color=['red', 'blue', 'green', 'orange', 'purple'])
            ))
            sample_tree.update_layout(
                title="Decision Flow Network (Sample)",
                showlegend=False,
                xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False)
            )
            st.plotly_chart(sample_tree, use_container_width=True)
    
    def _render_main_dashboard(self):
        """Render main dashboard content"""
        view_mode = st.session_state.get('view_mode', 'Overview')
        
        if view_mode == "Overview":
            self._render_overview()
        elif view_mode == "Episode Analysis":
            self._render_episode_analysis()
        elif view_mode == "Persona Evolution":
            self._render_persona_evolution()
        elif view_mode == "Decision Traceback":
            self._render_decision_traceback()
        elif view_mode == "Internal Metrics":
            self._render_internal_metrics()
        elif view_mode == "Comparative Analysis":
            self._render_comparative_analysis()
    
    def _render_overview(self):
        """Render overview dashboard"""
        st.header("📊 Journey Overview")
        
        # Key metrics
        summary = self.journey_data.get('summary_stats', {})
        episodes = self.journey_data.get('episodes', [])
        persona_states = self.journey_data.get('persona_evolution', [])
        
        # Top metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                "Total Episodes",
                summary.get('total_episodes', 0),
                help="Distinct health journey episodes"
            )
        
        with col2:
            avg_duration = summary.get('avg_episode_duration_hours', 0)
            st.metric(
                "Avg Episode Duration",
                f"{avg_duration:.1f}h",
                help="Average time to resolve episodes"
            )
        
        with col3:
            avg_response = summary.get('avg_response_time_minutes', 0)
            st.metric(
                "Avg Response Time",
                f"{avg_response:.0f}m",
                help="Average first response time"
            )
        
        with col4:
            member_initiated = summary.get('member_initiated_episodes', 0)
            total = summary.get('total_episodes', 1)
            st.metric(
                "Member Initiative",
                f"{member_initiated/total:.1%}",
                help="Percentage of member-initiated episodes"
            )
        
        # Main visualizations
        col1, col2 = st.columns([2, 1])
        
        with col1:
            # Episode timeline
            self._render_episode_timeline(episodes)
        
        with col2:
            # Episode outcomes distribution
            self._render_outcome_distribution(episodes)
        
        # Persona evolution summary
        st.subheader("👤 Persona Evolution Summary")
        if persona_states:
            latest_persona = persona_states[-1]
            initial_persona = persona_states[0]
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Current Engagement",
                    latest_persona['engagement_level'].title(),
                    delta=self._calculate_persona_change(initial_persona, latest_persona, 'engagement_level')
                )
            
            with col2:
                st.metric(
                    "Health Awareness",
                    latest_persona['health_awareness'].title(),
                    delta=self._calculate_persona_change(initial_persona, latest_persona, 'health_awareness')
                )
            
            with col3:
                st.metric(
                    "Trust Level",
                    latest_persona['trust_level'].title(),
                    delta=self._calculate_persona_change(initial_persona, latest_persona, 'trust_level')
                )
    
    def _render_episode_analysis(self):
        """Render episode analysis dashboard"""
        st.header("📋 Episode Analysis")
        
        episodes = self.journey_data.get('episodes', [])
        week_range = st.session_state.get('week_range', (1, 35))
        
        # Filter episodes by week range
        filtered_episodes = [
            ep for ep in episodes 
            if week_range[0] <= ep['week_range'][0] <= week_range[1]
        ]
        
        if not filtered_episodes:
            st.warning("No episodes found in the selected week range.")
            return
        
        # Episode selection
        st.subheader("Select Episode for Detailed Analysis")
        episode_options = {
            f"{ep['title']} (Week {ep['week_range'][0]})": ep 
            for ep in filtered_episodes
        }
        
        selected_episode_key = st.selectbox("Choose an episode:", list(episode_options.keys()))
        selected_episode = episode_options[selected_episode_key]
        
        # Episode details
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("📖 Episode Details")
            st.write(f"**Title:** {selected_episode['title']}")
            st.write(f"**Trigger:** {selected_episode['trigger_description']}")
            st.write(f"**Triggered by:** {selected_episode['triggered_by']}")
            st.write(f"**Duration:** {selected_episode['duration_days']} days")
            st.write(f"**Outcome:** {selected_episode['final_outcome']}")
            
            if selected_episode['friction_points']:
                st.write("**Friction Points:**")
                for fp in selected_episode['friction_points']:
                    st.write(f"- {fp}")
        
        with col2:
            st.subheader("📊 Episode Metrics")
            
            # Response time
            if selected_episode['response_time_minutes']:
                st.metric(
                    "First Response Time",
                    f"{selected_episode['response_time_minutes']:.0f} minutes"
                )
            
            # Resolution time
            if selected_episode['time_to_resolution_hours']:
                st.metric(
                    "Time to Resolution",
                    f"{selected_episode['time_to_resolution_hours']:.1f} hours"
                )
            
            # Agent involvement
            st.metric(
                "Agents Involved",
                len(selected_episode['agents_involved'])
            )
            
            # Message count
            st.metric(
                "Total Messages",
                selected_episode['message_count']
            )
        
        # Episode flow visualization
        st.subheader("🔄 Episode Message Flow")
        
        # Check if messages are available
        if 'messages' in selected_episode and selected_episode['messages']:
            messages_df = pd.DataFrame([
                {
                    "Timestamp": msg['timestamp'],
                    "Agent": msg.get('agent', msg['role']),
                    "Message": msg['text'][:100] + "..." if len(msg['text']) > 100 else msg['text'],
                    "Role": msg['role']
                }
                for msg in selected_episode['messages']
            ])
        else:
            st.warning("Message details not available for this episode.")
            messages_df = pd.DataFrame()  # Empty dataframe
        
        # Create message flow chart
        if not messages_df.empty:
            fig = go.Figure()
            
            for i, (_, row) in enumerate(messages_df.iterrows()):
                color = '#FF6B6B' if row['Role'] == 'member' else '#4ECDC4'
                fig.add_trace(go.Scatter(
                    x=[i],
                    y=[0],
                    mode='markers+text',
                    text=f"{row['Agent']}<br>{row['Message'][:30]}...",
                    textposition="top center",
                    marker=dict(size=20, color=color),
                    name=row['Role'],
                    showlegend=i == 0 or (i > 0 and messages_df.iloc[i-1]['Role'] != row['Role'])
                ))
            
            fig.update_layout(
                title="Message Flow Timeline",
                xaxis_title="Message Sequence",
                yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
                height=200
            )
            
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No message flow visualization available - episode summary only.")
        
        # All episodes summary
        episodes_df = pd.DataFrame(filtered_episodes)
        
        # Format for display
        display_df = episodes_df[[
            'title', 'trigger_type', 'triggered_by', 'duration_days',
            'response_time_minutes', 'time_to_resolution_hours', 'outcome_type'
        ]].copy()
        
        display_df.columns = [
            'Title', 'Trigger Type', 'Triggered By', 'Duration (days)',
            'Response Time (min)', 'Resolution Time (hrs)', 'Outcome'
        ]
        
        # Display table without PyArrow dependency
        st.subheader("Episodes Summary")
        for idx, row in display_df.iterrows():
            with st.expander(f"📋 {row['Title']}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Trigger Type:** {row['Trigger Type']}")
                    st.write(f"**Triggered By:** {row['Triggered By']}")
                    st.write(f"**Duration:** {row['Duration (days)']} days")
                with col2:
                    st.write(f"**Response Time:** {row['Response Time (min)']} min")
                    st.write(f"**Resolution Time:** {row['Resolution Time (hrs)']} hrs")
                    st.write(f"**Outcome:** {row['Outcome']}")
    
    def _render_persona_evolution(self):
        """Render persona evolution dashboard"""
        st.header("👤 Persona Evolution")
        
        persona_states = self.journey_data.get('persona_evolution', [])
        
        if not persona_states:
            st.warning("No persona evolution data available.")
            return
        
        # Create persona evolution timeline
        persona_df = pd.DataFrame(persona_states)
        
        # Engagement level over time
        st.subheader("📈 Engagement Level Evolution")
        
        # Map categorical values to numeric for visualization
        engagement_mapping = {'low': 1, 'medium': 2, 'high': 3}
        persona_df['engagement_numeric'] = persona_df['engagement_level'].map(engagement_mapping)
        
        fig_engagement = px.line(
            persona_df,
            x='week_index',
            y='engagement_numeric',
            title="Member Engagement Level Over Time",
            labels={'engagement_numeric': 'Engagement Level', 'week_index': 'Week'}
        )
        
        # Update y-axis to show categorical labels
        fig_engagement.update_layout(
            yaxis=dict(
                tickvals=[1, 2, 3],
                ticktext=['Low', 'Medium', 'High']
            )
        )
        
        st.plotly_chart(fig_engagement, use_container_width=True)
        
        # Multi-dimensional persona view
        st.subheader("🎯 Multi-Dimensional Persona Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Health awareness evolution
            awareness_mapping = {'passive': 1, 'reactive': 2, 'proactive': 3}
            persona_df['awareness_numeric'] = persona_df['health_awareness'].map(awareness_mapping)
            
            fig_awareness = px.line(
                persona_df,
                x='week_index',
                y='awareness_numeric',
                title="Health Awareness Evolution"
            )
            
            fig_awareness.update_layout(
                yaxis=dict(
                    tickvals=[1, 2, 3],
                    ticktext=['Passive', 'Reactive', 'Proactive']
                )
            )
            
            st.plotly_chart(fig_awareness, use_container_width=True)
        
        with col2:
            # Trust level evolution
            trust_mapping = {'skeptical': 1, 'building': 2, 'high': 3}
            persona_df['trust_numeric'] = persona_df['trust_level'].map(trust_mapping)
            
            fig_trust = px.line(
                persona_df,
                x='week_index',
                y='trust_numeric',
                title="Trust Level Evolution"
            )
            
            fig_trust.update_layout(
                yaxis=dict(
                    tickvals=[1, 2, 3],
                    ticktext=['Skeptical', 'Building', 'High']
                )
            )
            
            st.plotly_chart(fig_trust, use_container_width=True)
        
        # Current persona state
        st.subheader("📊 Current Persona State")
        
        if persona_states:
            latest_persona = persona_states[-1]
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Engagement", latest_persona['engagement_level'].title())
                st.metric("Health Awareness", latest_persona['health_awareness'].title())
            
            with col2:
                st.metric("Communication Style", latest_persona['communication_style'].title())
                st.metric("Trust Level", latest_persona['trust_level'].title())
            
            with col3:
                st.metric("Data Sharing", latest_persona['data_sharing_willingness'].title())
                st.metric("Initiative Taking", "Yes" if latest_persona['initiative_taking'] else "No")
            
            with col4:
                st.metric("Plan Confidence", f"{latest_persona['confidence_in_plan']:.1%}")
                st.metric("Follow-through", f"{latest_persona['follow_through_likelihood']:.1%}")
            
            # Primary concerns
            if latest_persona['primary_concerns']:
                st.write("**Primary Health Concerns:**")
                for concern in latest_persona['primary_concerns']:
                    st.write(f"- {concern.title()}")
    
    def _render_decision_traceback(self):
        """Render decision traceback dashboard"""
        st.header("🔍 Decision Traceback Analysis")
        
        # Load checkpoint files to get decision chains
        checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
        all_decisions = []
        
        for file_path in checkpoint_files:
            with open(file_path, 'r') as f:
                checkpoint = json.load(f)
                state = checkpoint['state']
                
                # Get all decision chains
                active_decisions = state.get('active_decision_chains', [])
                completed_decisions = state.get('completed_decision_chains', [])
                all_decisions.extend(active_decisions + completed_decisions)
        
        if not all_decisions:
            st.warning("No decision chains found in the data.")
            return
        
        # Decision selection
        st.subheader("Select Decision for Analysis")
        decision_options = {
            f"{decision.get('decision_id', 'Unknown')} - {decision.get('triggering_event', 'Unknown trigger')[:50]}...": decision
            for decision in all_decisions
        }
        
        selected_decision_key = st.selectbox("Choose a decision:", list(decision_options.keys()))
        selected_decision = decision_options[selected_decision_key]
        
        # Create decision visualization
        decision_viz = self.decision_visualizer.create_decision_tree(selected_decision)
        
        # Decision summary
        st.subheader("📋 Decision Summary")
        summary = decision_viz['summary']
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Priority", summary['priority'])
            st.metric("Status", summary['status'])
        
        with col2:
            st.metric("Agents Involved", len(summary['agents_involved']))
            st.metric("Evidence Count", summary['evidence_count'])
        
        with col3:
            st.metric("Risk Factors", summary['risk_factors_count'])
            st.metric("Avg Confidence", f"{summary['avg_confidence']:.1%}")
        
        with col4:
            st.metric("Implementation", summary['implementation_status'])
            st.metric("Follow-up Required", "Yes" if summary['follow_up_required'] else "No")
        
        # Decision network graph
        st.subheader("🕸️ Decision Flow Network")
        
        # Create network visualization using Plotly
        network_data = decision_viz['network_graph']
        
        fig_network = go.Figure()
        
        # Add edges
        for edge in network_data['edges']:
            fig_network.add_trace(go.Scatter(
                x=edge['x'],
                y=edge['y'],
                mode='lines',
                line=edge['line'],
                hoverinfo='text',
                text=edge.get('text', ''),
                showlegend=False
            ))
        
        # Add nodes
        fig_network.add_trace(go.Scatter(
            x=network_data['nodes']['x'],
            y=network_data['nodes']['y'],
            mode='markers+text',
            text=network_data['nodes']['text'],
            textposition="middle center",
            marker=network_data['nodes']['marker'],
            hovertemplate="<b>%{text}</b><br>%{customdata}<extra></extra>",
            customdata=[str(cd) for cd in network_data['nodes']['customdata']],
            showlegend=False
        ))
        
        fig_network.update_layout(network_data['layout'])
        fig_network.update_layout(height=600)
        
        st.plotly_chart(fig_network, use_container_width=True)
        
        # Decision timeline
        st.subheader("⏱️ Decision Timeline")
        timeline = decision_viz['timeline']
        
        timeline_df = pd.DataFrame(timeline['events'])
        
        if not timeline_df.empty:
            # Create timeline visualization
            fig_timeline = px.timeline(
                timeline_df,
                x_start="date",
                x_end="date",  # Point events
                y="event",
                color="type",
                title="Decision Process Timeline",
                hover_data=["agent", "description"]
            )
            
            st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Confidence analysis
        st.subheader("📊 Confidence Analysis")
        confidence_flow = decision_viz['confidence_flow']
        
        if confidence_flow['confidence_data']:
            confidence_df = pd.DataFrame(confidence_flow['confidence_data'])
            
            fig_confidence = px.bar(
                confidence_df,
                x='agent',
                y='confidence',
                color='analysis_type',
                title="Agent Confidence Levels",
                labels={'confidence': 'Confidence Level', 'agent': 'Agent'}
            )
            
            st.plotly_chart(fig_confidence, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Average Confidence", f"{confidence_flow['avg_confidence']:.1%}")
            with col2:
                st.metric("Confidence Variance", f"{confidence_flow['confidence_variance']:.3f}")
    
    def _render_internal_metrics(self):
        """Render internal metrics dashboard"""
        st.header("📊 Internal Metrics & Performance")
        
        metrics = self.journey_data.get('internal_metrics', [])
        
        if not metrics:
            st.warning("No internal metrics data available.")
            return
        
        # Create metrics dataframe
        metrics_df = pd.DataFrame(metrics)
        
        # Agent performance metrics
        st.subheader("👨‍⚕️ Agent Performance")
        
        # Aggregate agent hours across all weeks
        all_agent_hours = {}
        all_consultation_counts = {}
        
        for week_metrics in metrics:
            for agent, hours in week_metrics['agent_hours'].items():
                all_agent_hours[agent] = all_agent_hours.get(agent, 0) + hours
            
            for agent, count in week_metrics['consultation_count'].items():
                all_consultation_counts[agent] = all_consultation_counts.get(agent, 0) + count
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Agent hours chart
            if all_agent_hours:
                agent_hours_df = pd.DataFrame(list(all_agent_hours.items()), columns=['Agent', 'Total Hours'])
                
                fig_hours = px.bar(
                    agent_hours_df,
                    x='Agent',
                    y='Total Hours',
                    title="Total Agent Hours"
                )
                st.plotly_chart(fig_hours, use_container_width=True)
        
        with col2:
            # Consultation counts
            if all_consultation_counts:
                consultation_df = pd.DataFrame(list(all_consultation_counts.items()), columns=['Agent', 'Consultations'])
                
                fig_consultations = px.bar(
                    consultation_df,
                    x='Agent',
                    y='Consultations',
                    title="Total Consultations"
                )
                st.plotly_chart(fig_consultations, use_container_width=True)
        
        # Decision quality metrics over time
        st.subheader("🎯 Decision Quality Metrics")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if 'decision_confidence_avg' in metrics_df.columns:
                fig_confidence = px.line(
                    metrics_df,
                    x='week_index',
                    y='decision_confidence_avg',
                    title="Average Decision Confidence Over Time"
                )
                st.plotly_chart(fig_confidence, use_container_width=True)
        
        with col2:
            if 'decision_implementation_rate' in metrics_df.columns:
                fig_implementation = px.line(
                    metrics_df,
                    x='week_index',
                    y='decision_implementation_rate',
                    title="Decision Implementation Rate Over Time"
                )
                st.plotly_chart(fig_implementation, use_container_width=True)
        
        # Member engagement metrics
        st.subheader("👤 Member Engagement Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if 'member_initiative_messages' in metrics_df.columns:
                fig_initiative = px.bar(
                    metrics_df,
                    x='week_index',
                    y='member_initiative_messages',
                    title="Member Initiative Messages per Week"
                )
                st.plotly_chart(fig_initiative, use_container_width=True)
        
        with col2:
            if 'member_response_rate' in metrics_df.columns:
                fig_response_rate = px.line(
                    metrics_df,
                    x='week_index',
                    y='member_response_rate',
                    title="Member Response Rate Over Time"
                )
                st.plotly_chart(fig_response_rate, use_container_width=True)
        
        with col3:
            if 'member_question_complexity' in metrics_df.columns:
                fig_complexity = px.line(
                    metrics_df,
                    x='week_index',
                    y='member_question_complexity',
                    title="Question Complexity Over Time"
                )
                st.plotly_chart(fig_complexity, use_container_width=True)
        
        # Create summary table
        summary_columns = [
            'week_index', 'decision_confidence_avg', 'decision_implementation_rate',
            'member_initiative_messages', 'member_response_rate', 'member_question_complexity'
        ]
        
        available_columns = [col for col in summary_columns if col in metrics_df.columns]
        if available_columns:
            display_metrics = metrics_df[available_columns].copy()
            # Create new column names for available columns
            column_mapping = {
                'week_index': 'Week',
                'decision_confidence_avg': 'Avg Decision Confidence', 
                'decision_implementation_rate': 'Implementation Rate',
                'member_initiative_messages': 'Member Initiatives',
                'member_response_rate': 'Response Rate',
                'member_question_complexity': 'Question Complexity'
            }
            display_metrics.columns = [column_mapping.get(col, col) for col in available_columns]
            
            # Display metrics without PyArrow dependency
            st.subheader("📊 Weekly Metrics")
            for idx, row in display_metrics.iterrows():
                with st.expander(f"Week {row[display_metrics.columns[0]]}", expanded=False):
                    cols = st.columns(3)
                    for i, (col_name, value) in enumerate(row.items()):
                        if i == 0:  # Skip week column
                            continue
                        with cols[(i-1) % 3]:
                            if isinstance(value, float):
                                if 'Rate' in col_name or 'Confidence' in col_name:
                                    st.metric(col_name, f"{value:.1%}")
                                else:
                                    st.metric(col_name, f"{value:.2f}")
                            else:
                                st.metric(col_name, str(value))
        else:
            st.info("Detailed metrics table not available - summary metrics shown above.")
    
    def _render_comparative_analysis(self):
        """Render comparative analysis dashboard"""
        st.header("🔄 Comparative Analysis")
        
        episodes = self.journey_data.get('episodes', [])
        
        if not episodes:
            st.warning("No episode data available for comparison.")
            return
        
        episodes_df = pd.DataFrame(episodes)
        
        # Episode type comparison
        st.subheader("📊 Episode Type Analysis")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # Trigger type distribution
            trigger_counts = episodes_df['trigger_type'].value_counts()
            
            fig_triggers = px.pie(
                values=trigger_counts.values,
                names=trigger_counts.index,
                title="Episodes by Trigger Type"
            )
            st.plotly_chart(fig_triggers, use_container_width=True)
        
        with col2:
            # Outcome type distribution
            outcome_counts = episodes_df['outcome_type'].value_counts()
            
            fig_outcomes = px.pie(
                values=outcome_counts.values,
                names=outcome_counts.index,
                title="Episodes by Outcome Type"
            )
            st.plotly_chart(fig_outcomes, use_container_width=True)
        
        # Performance comparison
        st.subheader("⚡ Performance Comparison")
        
        # Response time vs resolution time scatter
        fig_performance = px.scatter(
            episodes_df,
            x='response_time_minutes',
            y='time_to_resolution_hours',
            color='trigger_type',
            size='message_count',
            hover_data=['title', 'outcome_type'],
            title="Response Time vs Resolution Time",
            labels={
                'response_time_minutes': 'First Response Time (minutes)',
                'time_to_resolution_hours': 'Total Resolution Time (hours)'
            }
        )
        
        st.plotly_chart(fig_performance, use_container_width=True)
        
        # Agent involvement analysis
        st.subheader("👥 Agent Collaboration Analysis")
        
        # Count agent involvement
        agent_involvement = {}
        for episode in episodes:
            for agent in episode['agents_involved']:
                agent_involvement[agent] = agent_involvement.get(agent, 0) + 1
        
        if agent_involvement:
            agent_df = pd.DataFrame(list(agent_involvement.items()), columns=['Agent', 'Episode Count'])
            
            fig_agents = px.bar(
                agent_df,
                x='Agent',
                y='Episode Count',
                title="Agent Involvement in Episodes"
            )
            st.plotly_chart(fig_agents, use_container_width=True)
        
        # Friction analysis
        st.subheader("⚠️ Friction Point Analysis")
        
        # Collect all friction points
        all_friction_points = []
        for episode in episodes:
            all_friction_points.extend(episode['friction_points'])
        
        if all_friction_points:
            friction_counts = pd.Series(all_friction_points).value_counts()
            
            fig_friction = px.bar(
                x=friction_counts.index,
                y=friction_counts.values,
                title="Most Common Friction Points"
            )
            fig_friction.update_xaxis(title="Friction Point Type")
            fig_friction.update_yaxis(title="Frequency")
            
            st.plotly_chart(fig_friction, use_container_width=True)
        else:
            st.info("No friction points detected in the analyzed episodes.")
        
        # Quality metrics comparison
        st.subheader("📈 Quality Metrics")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            avg_response_time = episodes_df['response_time_minutes'].mean()
            st.metric("Avg Response Time", f"{avg_response_time:.1f} min")
        
        with col2:
            avg_resolution_time = episodes_df['time_to_resolution_hours'].mean()
            st.metric("Avg Resolution Time", f"{avg_resolution_time:.1f} hrs")
        
        with col3:
            friction_rate = len([ep for ep in episodes if ep['friction_points']]) / len(episodes) if episodes else 0
            st.metric("Friction Rate", f"{friction_rate:.1%}")
    
    # Helper methods
    def _render_episode_timeline(self, episodes: List[Dict[str, Any]]):
        """Render episode timeline visualization"""
        if not episodes:
            return
        
        # Convert episodes to timeline format
        timeline_data = []
        for episode in episodes:
            start_date = datetime.fromisoformat(episode['start_date'])
            end_date = datetime.fromisoformat(episode['end_date'])
            
            timeline_data.append({
                'Episode': episode['title'],
                'Start': episode['start_date'],
                'End': episode['end_date'],
                'Duration': episode['duration_days'],
                'Type': episode['trigger_type'],
                'Outcome': episode['outcome_type']
            })
        
        timeline_df = pd.DataFrame(timeline_data)
        
        fig = px.timeline(
            timeline_df,
            x_start="Start",
            x_end="End",
            y="Episode",
            color="Type",
            title="Member Journey Timeline",
            hover_data=["Duration", "Outcome"]
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_outcome_distribution(self, episodes: List[Dict[str, Any]]):
        """Render outcome distribution chart"""
        if not episodes:
            return
        
        outcome_counts = {}
        for episode in episodes:
            outcome = episode['outcome_type']
            outcome_counts[outcome] = outcome_counts.get(outcome, 0) + 1
        
        fig = px.pie(
            values=list(outcome_counts.values()),
            names=list(outcome_counts.keys()),
            title="Episode Outcomes"
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _calculate_persona_change(self, initial: Dict, latest: Dict, attribute: str) -> str:
        """Calculate persona change delta"""
        initial_val = initial.get(attribute, '')
        latest_val = latest.get(attribute, '')
        
        if initial_val == latest_val:
            return None
        
        # Simple mapping for directional change
        improvement_map = {
            'engagement_level': {'low': 1, 'medium': 2, 'high': 3},
            'health_awareness': {'passive': 1, 'reactive': 2, 'proactive': 3},
            'trust_level': {'skeptical': 1, 'building': 2, 'high': 3}
        }
        
        if attribute in improvement_map:
            initial_score = improvement_map[attribute].get(initial_val, 0)
            latest_score = improvement_map[attribute].get(latest_val, 0)
            
            if latest_score > initial_score:
                return "Improved"
            elif latest_score < initial_score:
                return "Declined"
        
        return "Changed"

def main():
    """Main application entry point"""
    dashboard = AdvancedDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
