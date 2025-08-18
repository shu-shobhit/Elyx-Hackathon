#!/usr/bin/env python3
"""
Minimal Member Journey Dashboard
Core visualizations only, maximum compatibility
"""

import streamlit as st
import plotly.express as px
import json
import glob
from journey_analyzer import JourneyAnalyzer

def load_data():
    """Load and analyze journey data"""
    checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
    if not checkpoint_files:
        return None
    
    analyzer = JourneyAnalyzer()
    return analyzer.analyze_journey(checkpoint_files)

def main():
    st.set_page_config(page_title="Journey Dashboard", page_icon="📊")
    
    st.title("📊 Member Journey Dashboard")
    
    # Load data button
    if st.button("Load Journey Data"):
        with st.spinner("Loading..."):
            data = load_data()
            if data:
                st.session_state['data'] = data
                st.success("Data loaded successfully!")
                st.rerun()
            else:
                st.error("No data files found")
    
    # Show dashboard if data is loaded
    if 'data' in st.session_state:
        data = st.session_state['data']
        
        # Key metrics
        st.header("📋 Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            episodes = data.get('episodes', [])
            st.metric("Episodes", len(episodes))
        
        with col2:
            personas = data.get('persona_evolution', [])
            st.metric("Persona Changes", len(personas))
        
        with col3:
            metrics = data.get('internal_metrics', [])
            st.metric("Weeks", len(metrics))
        
        # Episodes by week
        if episodes:
            st.header("📅 Episodes by Week")
            
            week_data = {}
            for ep in episodes:
                week = ep['week_range'][0]
                week_data[week] = week_data.get(week, 0) + 1
            
            if week_data:
                weeks = list(week_data.keys())
                counts = list(week_data.values())
                
                fig = px.bar(x=weeks, y=counts, 
                           title="Number of Episodes per Week",
                           labels={'x': 'Week', 'y': 'Episodes'})
                st.plotly_chart(fig, use_container_width=True)
        
        # Engagement evolution
        if personas:
            st.header("👤 Member Engagement")
            
            engagement_map = {'low': 1, 'medium': 2, 'high': 3}
            weeks = [p['week_index'] for p in personas]
            engagement = [engagement_map.get(p['engagement_level'], 2) for p in personas]
            
            fig = px.line(x=weeks, y=engagement,
                         title="Engagement Level Over Time",
                         labels={'x': 'Week', 'y': 'Engagement Level'})
            
            fig.update_layout(yaxis=dict(
                tickvals=[1, 2, 3],
                ticktext=['Low', 'Medium', 'High']
            ))
            
            st.plotly_chart(fig, use_container_width=True)
        
        # Episode details
        if episodes:
            st.header("📋 Episode Details")
            
            for i, ep in enumerate(episodes[:5]):  # Show first 5
                with st.expander(f"{ep['title']} (Week {ep['week_range'][0]})"):
                    st.write(f"**Triggered by:** {ep['triggered_by']}")
                    st.write(f"**Duration:** {ep['duration_days']} days")
                    st.write(f"**Agents:** {', '.join(ep['agents_involved'])}")
                    st.write(f"**Outcome:** {ep['outcome_type']}")
            
            if len(episodes) > 5:
                st.info(f"Showing first 5 of {len(episodes)} episodes")
    
    else:
        st.info("Click 'Load Journey Data' to see visualizations")

if __name__ == "__main__":
    main()
