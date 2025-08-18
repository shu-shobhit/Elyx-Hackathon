#!/usr/bin/env python3
"""
Simple test dashboard to verify functionality
"""

import streamlit as st
import json
import glob
from journey_analyzer import JourneyAnalyzer

def main():
    st.set_page_config(page_title="Test Dashboard", layout="wide")
    st.title("🧪 Test Dashboard")
    
    # Initialize session state
    if 'data_loaded' not in st.session_state:
        st.session_state.data_loaded = False
        st.session_state.journey_data = None
    
    # Sidebar
    st.sidebar.header("🔧 Test Controls")
    
    # Check for checkpoint files
    checkpoint_files = glob.glob("checkpoints/week_*_checkpoint.json")
    st.sidebar.write(f"Found {len(checkpoint_files)} checkpoint files")
    
    # Load data button
    if st.sidebar.button("🔄 Load Test Data"):
        try:
            with st.spinner("Loading data..."):
                analyzer = JourneyAnalyzer()
                st.session_state.journey_data = analyzer.analyze_journey(checkpoint_files)
                st.session_state.data_loaded = True
                st.sidebar.success("✅ Data loaded!")
                st.rerun()  # Force refresh
        except Exception as e:
            st.sidebar.error(f"❌ Error: {str(e)}")
            st.sidebar.write("Traceback:")
            import traceback
            st.sidebar.code(traceback.format_exc())
    
    # Show dropdown if data is loaded
    if st.session_state.data_loaded and st.session_state.journey_data:
        st.sidebar.subheader("📊 Views Available")
        
        view_options = [
            "Overview",
            "Episode Analysis", 
            "Persona Evolution",
            "Decision Traceback",
            "Internal Metrics",
            "Comparative Analysis"
        ]
        
        selected_view = st.sidebar.selectbox("Choose View:", view_options)
        
        # Main content
        st.header(f"📋 {selected_view}")
        
        if selected_view == "Overview":
            show_overview(st.session_state.journey_data)
        elif selected_view == "Episode Analysis":
            show_episodes(st.session_state.journey_data)
        else:
            st.write(f"Showing {selected_view} view...")
            st.json({"status": "View available", "data_keys": list(st.session_state.journey_data.keys())})
    
    else:
        st.write("👆 Click 'Load Test Data' in the sidebar to begin")
        
        # Show what we expect to load
        if checkpoint_files:
            st.subheader("📁 Available Checkpoint Files:")
            for file in checkpoint_files:
                st.write(f"- {file}")

def show_overview(data):
    """Show overview data"""
    col1, col2, col3 = st.columns(3)
    
    episodes = data.get('episodes', [])
    personas = data.get('persona_evolution', [])
    metrics = data.get('internal_metrics', [])
    
    with col1:
        st.metric("Total Episodes", len(episodes))
    
    with col2:
        st.metric("Persona States", len(personas))
    
    with col3:
        st.metric("Metric Weeks", len(metrics))
    
    # Show sample data
    if episodes:
        st.subheader("📋 Episodes Found:")
        for i, ep in enumerate(episodes[:3]):  # Show first 3
            st.write(f"{i+1}. **{ep['title']}** (Week {ep['week_range'][0]})")
            st.write(f"   - Triggered by: {ep['triggered_by']}")
            st.write(f"   - Outcome: {ep['outcome_type']}")

def show_episodes(data):
    """Show episode analysis"""
    episodes = data.get('episodes', [])
    
    if not episodes:
        st.warning("No episodes found in data")
        return
    
    # Episode selector
    episode_options = {f"{ep['title']} (Week {ep['week_range'][0]})": ep for ep in episodes}
    selected_key = st.selectbox("Choose Episode:", list(episode_options.keys()))
    selected_episode = episode_options[selected_key]
    
    # Show episode details
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Title:**", selected_episode['title'])
        st.write("**Triggered by:**", selected_episode['triggered_by'])
        st.write("**Duration:**", f"{selected_episode['duration_days']} days")
        st.write("**Message count:**", selected_episode['message_count'])
    
    with col2:
        st.write("**Agents involved:**", ", ".join(selected_episode['agents_involved']))
        st.write("**Outcome:**", selected_episode['outcome_type'])
        if selected_episode['friction_points']:
            st.write("**Friction points:**")
            for fp in selected_episode['friction_points']:
                st.write(f"  - {fp}")

if __name__ == "__main__":
    main()
