#!/usr/bin/env python3
"""
Simple Member Journey Dashboard
Focused on core visualizations without complex dependencies
"""

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import json
import glob
from datetime import datetime
from journey_analyzer import JourneyAnalyzer

class SimpleDashboard:
    """Simple dashboard with core visualizations only"""
    
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
            page_title="Simple Journey Dashboard",
            page_icon="📊",
            layout="wide"
        )
        
        st.title("📊 Member Journey Dashboard")
        st.markdown("Simple visualization of member health journey")
        
        # Sidebar for data loading
        self._render_sidebar()
        
        # Main content
        if st.session_state.data_loaded and st.session_state.journey_data:
            self._render_dashboard()
        else:
            self._render_welcome()
    
    def _render_sidebar(self):
        """Simple sidebar for data loading"""
        st.sidebar.header("Data Controls")
        
        # Find checkpoint files
        checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
        
        if checkpoint_files:
            st.sidebar.success(f"Found {len(checkpoint_files)} files")
            
            if st.sidebar.button("Load Data"):
                with st.spinner("Loading..."):
                    journey_data = self.journey_analyzer.analyze_journey(checkpoint_files)
                    st.session_state.journey_data = journey_data
                    st.session_state.data_loaded = True
                st.sidebar.success("✅ Data loaded!")
                st.rerun()
        else:
            st.sidebar.warning("No checkpoint files found")
    
    def _render_welcome(self):
        """Welcome screen"""
        st.markdown("""
        ## Welcome to the Journey Dashboard
        
        This dashboard shows:
        - **Episode Timeline** - Key health conversations
        - **Persona Evolution** - How member engagement changes
        - **Agent Activity** - Team member involvement
        
        Use the sidebar to load your data.
        """)
    
    def _render_dashboard(self):
        """Main dashboard content"""
        data = st.session_state.journey_data
        
        # Overview metrics
        st.header("📋 Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_episodes = len(data.get('episodes', []))
            st.metric("Total Episodes", total_episodes)
        
        with col2:
            total_weeks = len(data.get('internal_metrics', []))
            st.metric("Weeks Analyzed", total_weeks)
        
        with col3:
            persona_points = len(data.get('persona_evolution', []))
            st.metric("Persona Changes", persona_points)
        
        with col4:
            summary = data.get('summary_stats', {})
            avg_response = summary.get('avg_response_time_minutes', 0)
            st.metric("Avg Response", f"{avg_response:.0f}m")
        
        # Episode Timeline
        st.header("📅 Episode Timeline")
        self._render_episode_timeline(data.get('episodes', []))
        
        # Persona Evolution (if available)
        persona_data = data.get('persona_evolution', [])
        if persona_data:
            st.header("👤 Member Engagement Over Time")
            self._render_persona_simple(persona_data)
        
        # Agent Activity
        metrics_data = data.get('internal_metrics', [])
        if metrics_data:
            st.header("👥 Agent Activity")
            self._render_agent_activity(metrics_data)
        
        # Episode List
        st.header("📋 All Episodes")
        self._render_episode_list(data.get('episodes', []))
    
    def _render_episode_timeline(self, episodes):
        """Simple timeline of episodes"""
        if not episodes:
            st.warning("No episodes found")
            return
        
        # Convert to DataFrame
        timeline_data = []
        for ep in episodes:
            timeline_data.append({
                'Title': ep['title'],
                'Start': ep['start_date'],
                'End': ep['end_date'],
                'Type': ep['trigger_type'],
                'Week': ep['week_range'][0]
            })
        
        df = pd.DataFrame(timeline_data)
        
        # Simple bar chart by week
        week_counts = df['Week'].value_counts().sort_index()
        
        fig = px.bar(
            x=week_counts.index,
            y=week_counts.values,
            title="Episodes by Week",
            labels={'x': 'Week', 'y': 'Number of Episodes'}
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_persona_simple(self, persona_data):
        """Simple persona evolution chart"""
        if not persona_data:
            return
        
        df = pd.DataFrame(persona_data)
        
        # Map engagement levels to numbers
        engagement_map = {'low': 1, 'medium': 2, 'high': 3}
        df['engagement_numeric'] = df['engagement_level'].map(engagement_map)
        
        fig = px.line(
            df,
            x='week_index',
            y='engagement_numeric',
            title="Member Engagement Level",
            labels={'week_index': 'Week', 'engagement_numeric': 'Engagement Level'}
        )
        
        # Update y-axis labels
        fig.update_layout(
            yaxis=dict(
                tickvals=[1, 2, 3],
                ticktext=['Low', 'Medium', 'High']
            )
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    def _render_agent_activity(self, metrics_data):
        """Simple agent activity visualization"""
        if not metrics_data:
            return
        
        # Aggregate agent hours
        all_agent_hours = {}
        for week_metrics in metrics_data:
            for agent, hours in week_metrics.get('agent_hours', {}).items():
                all_agent_hours[agent] = all_agent_hours.get(agent, 0) + hours
        
        if all_agent_hours:
            agents = list(all_agent_hours.keys())
            hours = list(all_agent_hours.values())
            
            fig = px.bar(
                x=agents,
                y=hours,
                title="Total Agent Hours",
                labels={'x': 'Agent', 'y': 'Hours'}
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def _render_episode_list(self, episodes):
        """Simple list of episodes"""
        if not episodes:
            st.warning("No episodes to display")
            return
        
        for i, ep in enumerate(episodes):
            with st.expander(f"Episode {i+1}: {ep['title']}", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Week:** {ep['week_range'][0]}-{ep['week_range'][1]}")
                    st.write(f"**Triggered by:** {ep['triggered_by']}")
                    st.write(f"**Duration:** {ep['duration_days']} days")
                
                with col2:
                    st.write(f"**Agents involved:** {', '.join(ep['agents_involved'])}")
                    st.write(f"**Messages:** {ep['message_count']}")
                    st.write(f"**Outcome:** {ep['outcome_type']}")
                
                if ep['friction_points']:
                    st.write("**Friction points:**")
                    for fp in ep['friction_points']:
                        st.write(f"• {fp}")

def main():
    """Main application entry point"""
    dashboard = SimpleDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()
