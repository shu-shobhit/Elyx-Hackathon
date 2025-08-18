#!/usr/bin/env python3
"""
Elyx Health Journey Visualization Dashboard
Comprehensive Streamlit app for visualizing member progress, decisions, and metrics
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import numpy as np
from typing import Dict, List, Any
import uuid

# Import our system components
from state import ConversationalState
from utils import get_decision_chain, get_active_decision_chains, get_completed_decision_chains

# Page configuration
st.set_page_config(
    page_title="Elyx Health Journey Dashboard",
    page_icon="🏥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #1f77b4;
    }
    .decision-card {
        background-color: #ffffff;
        padding: 1rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .timeline-container {
        background-color: #f8f9fa;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 2px solid #dee2e6;
    }
    .week-box {
        display: inline-block;
        width: 80px;
        height: 60px;
        margin: 5px;
        border: 2px solid #007bff;
        border-radius: 8px;
        text-align: center;
        line-height: 60px;
        font-weight: bold;
        background-color: #e3f2fd;
    }
    .week-completed {
        background-color: #d4edda;
        border-color: #28a745;
        color: #155724;
    }
    .week-in-progress {
        background-color: #fff3cd;
        border-color: #ffc107;
        color: #856404;
    }
    .week-scheduled {
        background-color: #f8d7da;
        border-color: #dc3545;
        color: #721c24;
    }
    .status-normal { color: #28a745; }
    .status-elevated { color: #ffc107; }
    .status-high { color: #dc3545; }
    .agent-metric {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .decision-detail {
        background-color: #f8f9fa;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 4px solid #007bff;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

def create_sample_decision_data():
    """Create comprehensive sample decision data"""
    
    decisions = [
        {
            "decision_id": "DC_W1_abc123",
            "title": "Glucose Management",
            "week": 1,
            "trigger": "Elevated fasting glucose (105 mg/dL)",
            "date": "Week 1, Day 3",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 85},
                {"name": "Carla", "role": "Nutrition", "confidence": 90},
                {"name": "Rachel", "role": "Exercise", "confidence": 88}
            ],
            "evidence": [
                "Blood panel: Fasting glucose 105 mg/dL",
                "Member symptoms: Fatigue after meals",
                "Previous history: Family diabetes risk"
            ],
            "final_decision": "Implement comprehensive nutrition protocol",
            "outcome": "Glucose improved to 95 mg/dL (Week 4)",
            "status": "completed",
            "impact": 15,
            "duration": 3
        },
        {
            "decision_id": "DC_W2_def456",
            "title": "Exercise Plan",
            "week": 2,
            "trigger": "Member wants to improve cardiovascular fitness",
            "date": "Week 2, Day 1",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Rachel", "role": "Exercise", "confidence": 92},
                {"name": "Carla", "role": "Nutrition", "confidence": 88}
            ],
            "evidence": [
                "Fitness Test: Current VO2 max 25 ml/kg/min (Poor)",
                "Member goals: Improve cardiovascular health",
                "Current activity: Sedentary lifestyle"
            ],
            "final_decision": "Progressive walking-to-jogging program",
            "outcome": "VO2 max improved to 32 ml/kg/min after 6 weeks",
            "status": "completed",
            "impact": 12,
            "duration": 6
        },
        {
            "decision_id": "DC_W3_ghi789",
            "title": "Sleep Issues",
            "week": 3,
            "trigger": "Member reports poor sleep quality",
            "date": "Week 3, Day 2",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 78},
                {"name": "Ruby", "role": "Wellness", "confidence": 85}
            ],
            "evidence": [
                "Sleep diary: 5-6 hours per night",
                "Stress levels: High work pressure",
                "Caffeine intake: 4 cups daily"
            ],
            "final_decision": "Sleep hygiene protocol + stress management",
            "outcome": "Sleep improved to 7-8 hours per night",
            "status": "completed",
            "impact": 10,
            "duration": 4
        },
        {
            "decision_id": "DC_W4_jkl012",
            "title": "Stress Management",
            "week": 4,
            "trigger": "High stress levels affecting health",
            "date": "Week 4, Day 1",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Ruby", "role": "Wellness", "confidence": 90},
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 82}
            ],
            "evidence": [
                "Stress assessment: High cortisol levels",
                "Work pressure: 60+ hour weeks",
                "Physical symptoms: Headaches, fatigue"
            ],
            "final_decision": "Mindfulness program + work-life balance coaching",
            "outcome": "Stress levels reduced by 40%",
            "status": "completed",
            "impact": 8,
            "duration": 4
        },
        {
            "decision_id": "DC_W5_mno345",
            "title": "Weight Loss",
            "week": 5,
            "trigger": "Member wants to lose 10 pounds",
            "date": "Week 5, Day 3",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Carla", "role": "Nutrition", "confidence": 95},
                {"name": "Rachel", "role": "Exercise", "confidence": 88}
            ],
            "evidence": [
                "Current weight: 180 lbs, Goal: 170 lbs",
                "Body composition: 25% body fat",
                "Metabolic rate: 1800 calories/day"
            ],
            "final_decision": "Calorie deficit + strength training program",
            "outcome": "Lost 8 pounds in 8 weeks",
            "status": "in_progress",
            "impact": 6,
            "duration": 8
        },
        {
            "decision_id": "DC_W6_pqr678",
            "title": "Review Session",
            "week": 6,
            "trigger": "Quarterly health review",
            "date": "Week 6, Day 1",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 88},
                {"name": "Carla", "role": "Nutrition", "confidence": 92},
                {"name": "Rachel", "role": "Exercise", "confidence": 85}
            ],
            "evidence": [
                "Overall health score: 85/100",
                "All previous interventions successful",
                "Member satisfaction: 4.8/5.0"
            ],
            "final_decision": "Continue current protocols, add maintenance plan",
            "outcome": "Health score maintained at 85+",
            "status": "scheduled",
            "impact": 5,
            "duration": 12
        },
        {
            "decision_id": "DC_W7_stu901",
            "title": "Blood Pressure Management",
            "week": 7,
            "trigger": "Elevated blood pressure readings",
            "date": "Week 7, Day 2",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 92},
                {"name": "Carla", "role": "Nutrition", "confidence": 87}
            ],
            "evidence": [
                "BP readings: 140/90 mmHg consistently",
                "Family history: Hypertension",
                "Lifestyle factors: High sodium diet"
            ],
            "final_decision": "DASH diet + regular monitoring",
            "outcome": "BP reduced to 130/85 mmHg",
            "status": "completed",
            "impact": 9,
            "duration": 4
        },
        {
            "decision_id": "DC_W8_vwx234",
            "title": "Mental Health Support",
            "week": 8,
            "trigger": "Member reports anxiety symptoms",
            "date": "Week 8, Day 1",
            "member": "Rohan Patel",
            "agents": [
                {"name": "Ruby", "role": "Wellness", "confidence": 89},
                {"name": "Dr. Warren", "role": "Clinical", "confidence": 85}
            ],
            "evidence": [
                "Anxiety assessment: Moderate symptoms",
                "Work stress: High pressure environment",
                "Sleep quality: Improving but still issues"
            ],
            "final_decision": "Cognitive behavioral therapy + meditation",
            "outcome": "Anxiety symptoms reduced by 60%",
            "status": "in_progress",
            "impact": 7,
            "duration": 6
        }
    ]
    
    return decisions

def create_agent_performance_data():
    """Create sample agent performance data"""
    
    agents = {
        "Dr. Warren": {
            "decisions": 15,
            "avg_confidence": 87,
            "success_rate": 92,
            "recent_decisions": [
                {"title": "Glucose Mgmt (Week 1)", "status": "successful"},
                {"title": "Sleep Issues (Week 3)", "status": "successful"},
                {"title": "Stress Mgmt (Week 4)", "status": "successful"}
            ]
        },
        "Carla": {
            "decisions": 23,
            "avg_confidence": 91,
            "success_rate": 89,
            "recent_decisions": [
                {"title": "Low GI Diet (Week 1)", "status": "successful"},
                {"title": "Meal Timing (Week 2)", "status": "successful"},
                {"title": "Supplement Plan (Week 5)", "status": "in_progress"}
            ]
        },
        "Rachel": {
            "decisions": 18,
            "avg_confidence": 88,
            "success_rate": 94,
            "recent_decisions": [
                {"title": "Exercise Plan (Week 2)", "status": "successful"},
                {"title": "Strength Training (Week 5)", "status": "in_progress"},
                {"title": "Cardio Program (Week 3)", "status": "successful"}
            ]
        },
        "Ruby": {
            "decisions": 12,
            "avg_confidence": 85,
            "success_rate": 91,
            "recent_decisions": [
                {"title": "Stress Mgmt (Week 4)", "status": "successful"},
                {"title": "Sleep Hygiene (Week 3)", "status": "successful"},
                {"title": "Mindfulness (Week 5)", "status": "in_progress"}
            ]
        }
    }
    
    return agents

def display_health_journey_timeline():
    """Display the health journey timeline visualization"""
    st.header("🏥 ROHAN PATEL - HEALTH JOURNEY TIMELINE")
    
    # Create timeline container
    st.markdown("""
    <div class="timeline-container">
        <div style="text-align: center; margin-bottom: 1rem;">
            <strong>Week 1</strong> &nbsp;&nbsp;&nbsp; <strong>Week 2</strong> &nbsp;&nbsp;&nbsp; <strong>Week 3</strong> &nbsp;&nbsp;&nbsp; <strong>Week 4</strong> &nbsp;&nbsp;&nbsp; <strong>Week 5</strong> &nbsp;&nbsp;&nbsp; <strong>Week 6</strong> &nbsp;&nbsp;&nbsp; <strong>Week 7</strong> &nbsp;&nbsp;&nbsp; <strong>Week 8</strong>
        </div>
        <div style="text-align: center; margin-bottom: 1rem;">
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #28a745; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #28a745; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #28a745; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #28a745; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #ffc107; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #6c757d; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #28a745; border-radius: 50%; margin: 0 5px;"></span>
            <span style="display: inline-block; width: 20px; height: 20px; background-color: #ffc107; border-radius: 50%; margin: 0 5px;"></span>
        </div>
        <div style="text-align: center;">
            <div class="week-box week-completed">DC_1<br>Glucose<br>Mgmt</div>
            <div class="week-box week-completed">DC_2<br>Exercise<br>Plan</div>
            <div class="week-box week-completed">DC_3<br>Sleep<br>Issues</div>
            <div class="week-box week-completed">DC_4<br>Stress<br>Mgmt</div>
            <div class="week-box week-in-progress">DC_5<br>Weight<br>Loss</div>
            <div class="week-box week-scheduled">DC_6<br>Review<br>Session</div>
            <div class="week-box week-completed">DC_7<br>BP<br>Mgmt</div>
            <div class="week-box week-in-progress">DC_8<br>Mental<br>Health</div>
        </div>
        <div style="text-align: center; margin-top: 1rem;">
            <span style="color: #28a745;">✅</span> <span style="margin-right: 20px;">Completed</span>
            <span style="color: #ffc107;">🔄</span> <span style="margin-right: 20px;">In Progress</span>
            <span style="color: #6c757d;">📅</span> <span>Scheduled</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_decision_detail(decision):
    """Display detailed decision information"""
    st.markdown(f"""
    <div class="decision-detail">
        <h3>DECISION: {decision['decision_id']} - {decision['title']}</h3>
        <p><strong>🚨 TRIGGER:</strong> {decision['trigger']}</p>
        <p><strong>📅 DATE:</strong> {decision['date']}</p>
        <p><strong>👤 MEMBER:</strong> {decision['member']}</p>
        
        <p><strong>🏥 AGENTS INVOLVED:</strong></p>
        <div style="display: flex; gap: 10px; margin-bottom: 1rem;">
    """, unsafe_allow_html=True)
    
    for agent in decision['agents']:
        status_color = "#28a745" if decision['status'] == 'completed' else "#ffc107"
        st.markdown(f"""
        <div style="flex: 1; text-align: center; padding: 10px; background-color: {status_color}; color: white; border-radius: 5px;">
            <strong>{agent['name']}</strong><br>
            ({agent['role']})<br>
            {agent['confidence']}% confidence
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("""
        </div>
        <p><strong>📋 EVIDENCE CONSIDERED:</strong></p>
        <ul>
    """, unsafe_allow_html=True)
    
    for evidence in decision['evidence']:
        st.markdown(f"<li>{evidence}</li>", unsafe_allow_html=True)
    
    st.markdown(f"""
        </ul>
        <p><strong>🎯 FINAL DECISION:</strong> {decision['final_decision']}</p>
        <p><strong>✅ OUTCOME:</strong> {decision['outcome']}</p>
    </div>
    """, unsafe_allow_html=True)

def display_decision_flow_diagram():
    """Display decision flow diagram"""
    st.header("🔄 Decision Flow Process")
    
    # Create a simple flow diagram using HTML/CSS
    st.markdown("""
    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
            <div style="background-color: #007bff; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>TRIGGER</strong><br>Elevated Glucose
            </div>
            <div style="font-size: 24px;">→</div>
            <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>ANALYSIS</strong><br>Dr. Warren<br>Carla<br>Rachel
            </div>
            <div style="font-size: 24px;">→</div>
            <div style="background-color: #ffc107; color: black; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>DECISION</strong><br>Nutrition Protocol
            </div>
        </div>
        
        <div style="display: flex; justify-content: center; align-items: center;">
            <div style="background-color: #6c757d; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>EVIDENCE</strong><br>Test Results<br>Symptoms<br>Feedback
            </div>
            <div style="font-size: 24px;">←</div>
            <div style="background-color: #17a2b8; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>OUTCOME</strong><br>Improved Glucose
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def display_agent_performance_metrics(agents):
    """Display agent performance metrics"""
    st.header("📊 AGENT PERFORMANCE METRICS")
    
    for agent_name, metrics in agents.items():
        st.markdown(f"""
        <div class="agent-metric">
            <h3>{agent_name} ({'Medical Strategist' if 'Warren' in agent_name else 'Nutritionist' if 'Carla' in agent_name else 'Exercise Specialist' if 'Rachel' in agent_name else 'Wellness Coach'})</h3>
            <div style="display: flex; gap: 20px; margin-bottom: 1rem;">
                <div><strong>Decisions:</strong> {metrics['decisions']}</div>
                <div><strong>Avg Confidence:</strong> {metrics['avg_confidence']}%</div>
                <div><strong>Success Rate:</strong> {metrics['success_rate']}%</div>
            </div>
            <div style="border-top: 1px solid rgba(255,255,255,0.3); padding-top: 10px;">
                <strong>Recent Decisions:</strong><br>
        """, unsafe_allow_html=True)
        
        for decision in metrics['recent_decisions']:
            status_icon = "✅" if decision['status'] == 'successful' else "🔄"
            st.markdown(f"• {decision['title']} - {status_icon} {decision['status'].title()}", unsafe_allow_html=True)
        
        st.markdown("</div></div>", unsafe_allow_html=True)

def display_confidence_vs_outcomes_chart():
    """Display confidence vs outcomes scatter plot"""
    st.header("📈 DECISION CONFIDENCE vs OUTCOMES")
    
    # Create sample data for confidence vs outcomes
    np.random.seed(42)
    n_points = 20
    
    # Generate realistic data
    confidence_levels = np.random.uniform(60, 95, n_points)
    outcomes = np.random.choice(['successful', 'unsuccessful'], n_points, p=[0.8, 0.2])
    
    # Create scatter plot
    fig = go.Figure()
    
    successful_mask = [outcome == 'successful' for outcome in outcomes]
    unsuccessful_mask = [outcome == 'unsuccessful' for outcome in outcomes]
    
    fig.add_trace(go.Scatter(
        x=confidence_levels[successful_mask],
        y=[85 + np.random.normal(0, 5) for _ in range(sum(successful_mask))],
        mode='markers',
        name='Successful Outcome',
        marker=dict(color='#28a745', size=12, symbol='circle'),
        hovertemplate='Confidence: %{x:.1f}%<br>Outcome Score: %{y:.1f}<extra></extra>'
    ))
    
    fig.add_trace(go.Scatter(
        x=confidence_levels[unsuccessful_mask],
        y=[30 + np.random.normal(0, 5) for _ in range(sum(unsuccessful_mask))],
        mode='markers',
        name='Unsuccessful Outcome',
        marker=dict(color='#dc3545', size=12, symbol='x'),
        hovertemplate='Confidence: %{x:.1f}%<br>Outcome Score: %{y:.1f}<extra></extra>'
    ))
    
    fig.update_layout(
        xaxis_title="Confidence Level (%)",
        yaxis_title="Outcome Score",
        xaxis=dict(range=[50, 100]),
        yaxis=dict(range=[0, 100]),
        height=400,
        showlegend=True
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_decision_explorer(decisions):
    """Display interactive decision explorer"""
    st.header("🔍 DECISION EXPLORER")
    
    # Search and filter options
    col1, col2 = st.columns([2, 1])
    
    with col1:
        search_term = st.text_input("🔍 SEARCH:", placeholder="Type decision ID or keywords...")
    
    with col2:
        status_filter = st.selectbox("📊 FILTERS:", ["All", "Completed", "In Progress", "Scheduled"])
    
    # Filter decisions based on search and status
    filtered_decisions = decisions
    if search_term:
        filtered_decisions = [d for d in decisions if search_term.lower() in d['decision_id'].lower() or search_term.lower() in d['title'].lower()]
    
    if status_filter != "All":
        filtered_decisions = [d for d in filtered_decisions if d['status'] == status_filter.lower().replace(" ", "_")]
    
    # Display decision list
    st.markdown("📋 DECISION LIST:")
    
    for decision in filtered_decisions:
        status_icon = "✅" if decision['status'] == 'completed' else "🔄" if decision['status'] == 'in_progress' else "📅"
        status_text = decision['status'].replace('_', ' ').title()
        
        with st.expander(f"{decision['decision_id']} | {decision['title']} | {decision['agents'][0]['name']} | {status_icon} {status_text}"):
            display_decision_detail(decision)

def display_health_trajectory(decisions):
    """Display health trajectory chart"""
    st.header("📈 ROHAN'S HEALTH TRAJECTORY")
    
    # Create health score data over time
    weeks = list(range(1, 9))
    base_score = 70
    
    # Calculate health scores based on decision impacts
    health_scores = [base_score]
    for i, week in enumerate(weeks[1:], 1):
        # Find decisions up to this week
        week_decisions = [d for d in decisions if d['week'] <= week and d['status'] == 'completed']
        total_impact = sum(d['impact'] for d in week_decisions)
        new_score = min(100, base_score + total_impact)
        health_scores.append(new_score)
    
    # Create the trajectory chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=weeks,
        y=health_scores,
        mode='lines+markers',
        name='Health Score',
        line=dict(color='#1f77b4', width=4),
        marker=dict(size=10, color='#1f77b4')
    ))
    
    # Add decision points
    decision_points = []
    for decision in decisions:
        if decision['status'] == 'completed':
            decision_points.append({
                'week': decision['week'],
                'title': decision['title'],
                'impact': decision['impact']
            })
    
    for point in decision_points:
        fig.add_annotation(
            x=point['week'],
            y=health_scores[point['week'] - 1],
            text=f"• {point['title']}<br>(+{point['impact']} pts)",
            showarrow=True,
            arrowhead=2,
            arrowsize=1,
            arrowwidth=2,
            arrowcolor="#ff7f0e",
            ax=0,
            ay=-40
        )
    
    fig.update_layout(
        xaxis_title="Week",
        yaxis_title="Health Score",
        yaxis=dict(range=[60, 100]),
        height=400,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Decision points summary
    st.markdown("🎯 DECISION POINTS:")
    for point in decision_points:
        st.markdown(f"• Week {point['week']}: {point['title']} (DC_{point['week']})")
    
    st.markdown("📈 TREND: Steady improvement with targeted interventions")

def display_decision_impact_analysis(decisions):
    """Display decision impact analysis"""
    st.header("📊 DECISION IMPACT ANALYSIS")
    
    # Get completed decisions sorted by impact
    completed_decisions = [d for d in decisions if d['status'] == 'completed']
    completed_decisions.sort(key=lambda x: x['impact'], reverse=True)
    
    st.markdown("Most Impactful Decisions:")
    
    for i, decision in enumerate(completed_decisions[:3], 1):
        medal = "🥇" if i == 1 else "🥈" if i == 2 else "🥉"
        st.markdown(f"""
        <div style="background-color: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px; border-left: 4px solid #007bff;">
            <h4>{medal} {decision['title']} ({decision['decision_id']})</h4>
            <p><strong>Impact:</strong> +{decision['impact']} health points</p>
            <p><strong>Duration:</strong> {decision['duration']} weeks to see results</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("💡 INSIGHT: Medical interventions show fastest impact, lifestyle changes show sustained improvement")

def display_decision_overview(decisions):
    """Display overview of all decisions in a table format"""
    st.header("📋 ALL DECISIONS OVERVIEW")
    
    # Create a DataFrame for better display
    df_data = []
    for decision in decisions:
        status_icon = "✅" if decision['status'] == 'completed' else "🔄" if decision['status'] == 'in_progress' else "📅"
        agents_str = ", ".join([agent['name'] for agent in decision['agents']])
        
        df_data.append({
            "Decision ID": decision['decision_id'],
            "Title": decision['title'],
            "Week": decision['week'],
            "Status": f"{status_icon} {decision['status'].replace('_', ' ').title()}",
            "Agents": agents_str,
            "Impact": f"+{decision['impact']} pts",
            "Duration": f"{decision['duration']} weeks"
        })
    
    df = pd.DataFrame(df_data)
    
    # Add filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        status_filter = st.selectbox("Filter by Status:", ["All"] + list(set([d['status'] for d in decisions])))
    
    with col2:
        week_filter = st.selectbox("Filter by Week:", ["All"] + list(set([d['week'] for d in decisions])))
    
    with col3:
        agent_filter = st.selectbox("Filter by Agent:", ["All"] + list(set([agent['name'] for d in decisions for agent in d['agents']])))
    
    # Apply filters
    filtered_df = df.copy()
    if status_filter != "All":
        filtered_df = filtered_df[filtered_df['Status'].str.contains(status_filter.replace('_', ' ').title())]
    
    if week_filter != "All":
        filtered_df = filtered_df[filtered_df['Week'] == week_filter]
    
    if agent_filter != "All":
        filtered_df = filtered_df[filtered_df['Agents'].str.contains(agent_filter)]
    
    # Display the table
    st.dataframe(filtered_df, use_container_width=True)
    
    # Summary statistics
    st.subheader("📊 Summary Statistics")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Decisions", len(decisions))
    
    with col2:
        completed = len([d for d in decisions if d['status'] == 'completed'])
        st.metric("Completed", completed)
    
    with col3:
        in_progress = len([d for d in decisions if d['status'] == 'in_progress'])
        st.metric("In Progress", in_progress)
    
    with col4:
        total_impact = sum([d['impact'] for d in decisions if d['status'] == 'completed'])
        st.metric("Total Impact", f"+{total_impact} pts")

def display_single_decision_detail(decision):
    """Display detailed view of a single decision"""
    st.header(f"🔍 DECISION DETAIL: {decision['decision_id']}")
    
    # Decision header
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Decision ID", decision['decision_id'])
        st.metric("Week", decision['week'])
    
    with col2:
        status_icon = "✅" if decision['status'] == 'completed' else "🔄" if decision['status'] == 'in_progress' else "📅"
        st.metric("Status", f"{status_icon} {decision['status'].replace('_', ' ').title()}")
        st.metric("Impact", f"+{decision['impact']} pts")
    
    with col3:
        st.metric("Duration", f"{decision['duration']} weeks")
        st.metric("Agents", len(decision['agents']))
    
    # Detailed information
    st.subheader("📋 Decision Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("**🚨 Triggering Event:**")
        st.info(decision['trigger'])
        
        st.markdown("**📅 Date:**")
        st.write(decision['date'])
        
        st.markdown("**👤 Member:**")
        st.write(decision['member'])
    
    with col2:
        st.markdown("**🎯 Final Decision:**")
        st.success(decision['final_decision'])
        
        st.markdown("**✅ Outcome:**")
        st.write(decision['outcome'])
    
    # Agents involved
    st.subheader("🏥 Agents Involved")
    agent_cols = st.columns(len(decision['agents']))
    
    for i, agent in enumerate(decision['agents']):
        with agent_cols[i]:
            st.markdown(f"""
            <div style="background-color: #e3f2fd; padding: 15px; border-radius: 8px; text-align: center; border-left: 4px solid #2196f3;">
                <h4>{agent['name']}</h4>
                <p><strong>Role:</strong> {agent['role']}</p>
                <p><strong>Confidence:</strong> {agent['confidence']}%</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Evidence considered
    st.subheader("📋 Evidence Considered")
    for evidence in decision['evidence']:
        st.markdown(f"• {evidence}")
    
    # Decision flow diagram for this specific decision
    st.subheader("🔄 Decision Flow")
    st.markdown(f"""
    <div style="text-align: center; padding: 20px; background-color: #f8f9fa; border-radius: 10px;">
        <div style="display: flex; justify-content: center; align-items: center; margin-bottom: 20px;">
            <div style="background-color: #dc3545; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>TRIGGER</strong><br>{decision['trigger'][:30]}...
            </div>
            <div style="font-size: 24px;">→</div>
            <div style="background-color: #28a745; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>ANALYSIS</strong><br>{', '.join([agent['name'] for agent in decision['agents']])}
            </div>
            <div style="font-size: 24px;">→</div>
            <div style="background-color: #ffc107; color: black; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>DECISION</strong><br>{decision['final_decision'][:30]}...
            </div>
        </div>
        
        <div style="display: flex; justify-content: center; align-items: center;">
            <div style="background-color: #6c757d; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>EVIDENCE</strong><br>{len(decision['evidence'])} items
            </div>
            <div style="font-size: 24px;">←</div>
            <div style="background-color: #17a2b8; color: white; padding: 15px; border-radius: 10px; margin: 0 10px;">
                <strong>OUTCOME</strong><br>{decision['outcome'][:30]}...
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main function to run the Streamlit app"""
    
    # Create sample data
    decisions = create_sample_decision_data()
    agents = create_agent_performance_data()
    
    # Display header
    st.markdown('<h1 class="main-header">🏥 Elyx Health Journey Dashboard</h1>', unsafe_allow_html=True)
    st.markdown("---")
    
    # Create sidebar navigation with decision ID selector
    st.sidebar.title("Navigation")
    
    # Decision ID selector
    st.sidebar.subheader("🎯 Select Decision ID")
    decision_ids = [d['decision_id'] for d in decisions]
    selected_decision_id = st.sidebar.selectbox(
        "Choose Decision ID:",
        ["All Decisions"] + decision_ids
    )
    
    # Main navigation
    page = st.sidebar.selectbox(
        "Choose a page:",
        ["Decision Overview", "Health Journey Timeline", "Decision Explorer", "Agent Performance", "Health Trajectory", "Impact Analysis"]
    )
    
    # Display appropriate content based on selection
    if page == "Decision Overview":
        if selected_decision_id == "All Decisions":
            display_decision_overview(decisions)
        else:
            # Find the selected decision
            selected_decision = next((d for d in decisions if d['decision_id'] == selected_decision_id), None)
            if selected_decision:
                display_single_decision_detail(selected_decision)
            else:
                st.error("Decision not found!")
                
    elif page == "Health Journey Timeline":
        display_health_journey_timeline()
        
        # Show selected decision detail if one is selected
        if selected_decision_id != "All Decisions":
            selected_decision = next((d for d in decisions if d['decision_id'] == selected_decision_id), None)
            if selected_decision:
                st.markdown("---")
                display_decision_detail(selected_decision)
                display_decision_flow_diagram()
            
    elif page == "Decision Explorer":
        display_decision_explorer(decisions)
        
    elif page == "Agent Performance":
        display_agent_performance_metrics(agents)
        st.markdown("---")
        display_confidence_vs_outcomes_chart()
        
    elif page == "Health Trajectory":
        display_health_trajectory(decisions)
        
    elif page == "Impact Analysis":
        display_decision_impact_analysis(decisions)
    
    # Quick navigation buttons
    st.sidebar.markdown("---")
    st.sidebar.subheader("🚀 Quick Navigation")
    
    if st.sidebar.button("📊 View All Decisions"):
        st.experimental_rerun()
    
    if st.sidebar.button("📈 View Health Trajectory"):
        st.experimental_rerun()
    
    # Footer
    st.markdown("---")
    st.markdown("**Elyx Health Journey Dashboard** - Built with Streamlit and Plotly")

if __name__ == "__main__":
    main()
