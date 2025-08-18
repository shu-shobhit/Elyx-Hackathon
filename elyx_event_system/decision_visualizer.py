#!/usr/bin/env python3
"""
Decision Traceback Visualization System
Creates interactive visualizations to trace why decisions were made
"""

import json
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import pandas as pd
import networkx as nx
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class DecisionNode:
    """Represents a node in the decision tree"""
    node_id: str
    node_type: str  # "trigger", "evidence", "analysis", "decision", "outcome"
    title: str
    description: str
    timestamp: str
    agent: Optional[str]
    confidence: Optional[float]
    importance: float  # 0.0 to 1.0
    metadata: Dict[str, Any]

@dataclass
class DecisionEdge:
    """Represents a connection between decision nodes"""
    source: str
    target: str
    relationship: str  # "triggered_by", "supported_by", "led_to", "influenced"
    strength: float  # 0.0 to 1.0
    description: str

class DecisionVisualizer:
    """Creates visualizations for decision traceability"""
    
    def __init__(self):
        self.decision_trees = {}
        self.timeline_data = []
    
    def create_decision_tree(self, decision_chain: Dict[str, Any]) -> Dict[str, Any]:
        """Create a decision tree visualization for a specific decision"""
        decision_id = decision_chain.get('decision_id', 'unknown')
        
        # Extract nodes and edges
        nodes = self._extract_decision_nodes(decision_chain)
        edges = self._extract_decision_edges(decision_chain, nodes)
        
        # Create network graph
        graph_data = self._create_network_graph(nodes, edges)
        
        # Create timeline
        timeline_data = self._create_decision_timeline(decision_chain)
        
        # Create confidence flow
        confidence_flow = self._create_confidence_flow(decision_chain)
        
        return {
            "decision_id": decision_id,
            "network_graph": graph_data,
            "timeline": timeline_data,
            "confidence_flow": confidence_flow,
            "summary": self._create_decision_summary(decision_chain)
        }
    
    def _extract_decision_nodes(self, decision_chain: Dict[str, Any]) -> List[DecisionNode]:
        """Extract all nodes involved in the decision"""
        nodes = []
        
        # Root trigger node
        trigger_node = DecisionNode(
            node_id=f"trigger_{decision_chain['decision_id']}",
            node_type="trigger",
            title="Triggering Event",
            description=decision_chain.get('triggering_event', 'Unknown trigger'),
            timestamp=decision_chain.get('created_at', ''),
            agent=None,
            confidence=None,
            importance=1.0,
            metadata={"priority": decision_chain.get('priority', 'Medium')}
        )
        nodes.append(trigger_node)
        
        # Evidence nodes
        for i, evidence in enumerate(decision_chain.get('evidence_considered', [])):
            evidence_node = DecisionNode(
                node_id=f"evidence_{decision_chain['decision_id']}_{i}",
                node_type="evidence",
                title=f"Evidence: {evidence.get('evidence_type', 'Unknown')}",
                description=evidence.get('description', ''),
                timestamp=evidence.get('timestamp', ''),
                agent=evidence.get('source', ''),
                confidence=evidence.get('confidence', 0.5),
                importance=evidence.get('relevance_score', 0.5),
                metadata=evidence
            )
            nodes.append(evidence_node)
        
        # Agent analysis nodes
        for i, analysis in enumerate(decision_chain.get('agent_analyses', [])):
            analysis_node = DecisionNode(
                node_id=f"analysis_{decision_chain['decision_id']}_{i}",
                node_type="analysis",
                title=f"Analysis by {analysis.get('agent_name', 'Unknown')}",
                description=f"{analysis.get('analysis_type', '')}: {', '.join(analysis.get('key_findings', [])[:2])}",
                timestamp=analysis.get('timestamp', ''),
                agent=analysis.get('agent_name', ''),
                confidence=analysis.get('confidence_level', 0.5),
                importance=analysis.get('confidence_level', 0.5),
                metadata=analysis
            )
            nodes.append(analysis_node)
        
        # Risk assessment nodes
        for i, risk in enumerate(decision_chain.get('risk_assessments', [])):
            risk_node = DecisionNode(
                node_id=f"risk_{decision_chain['decision_id']}_{i}",
                node_type="risk",
                title=f"Risk: {risk.get('risk_factor', 'Unknown')}",
                description=f"{risk.get('risk_level', 'Unknown')} risk - {risk.get('probability', 0.5):.1%} probability",
                timestamp=decision_chain.get('created_at', ''),
                agent=None,
                confidence=risk.get('probability', 0.5),
                importance=self._calculate_risk_importance(risk),
                metadata=risk
            )
            nodes.append(risk_node)
        
        # Final decision node
        decision_node = DecisionNode(
            node_id=f"decision_{decision_chain['decision_id']}",
            node_type="decision",
            title="Final Decision",
            description=decision_chain.get('final_decision', 'Decision pending'),
            timestamp=decision_chain.get('decision_timestamp', ''),
            agent=decision_chain.get('decision_maker', ''),
            confidence=None,
            importance=1.0,
            metadata={
                "rationale": decision_chain.get('decision_rationale', ''),
                "implementation_status": decision_chain.get('implementation_status', '')
            }
        )
        nodes.append(decision_node)
        
        # Outcome node (if available)
        if decision_chain.get('outcome_summary'):
            outcome_node = DecisionNode(
                node_id=f"outcome_{decision_chain['decision_id']}",
                node_type="outcome",
                title="Outcome",
                description=decision_chain.get('outcome_summary', ''),
                timestamp=decision_chain.get('updated_at', ''),
                agent=None,
                confidence=None,
                importance=0.8,
                metadata=decision_chain.get('outcome_metrics', {})
            )
            nodes.append(outcome_node)
        
        return nodes
    
    def _extract_decision_edges(self, decision_chain: Dict[str, Any], nodes: List[DecisionNode]) -> List[DecisionEdge]:
        """Extract relationships between decision nodes"""
        edges = []
        decision_id = decision_chain['decision_id']
        
        # Find specific node types
        trigger_node = next((n for n in nodes if n.node_type == "trigger"), None)
        evidence_nodes = [n for n in nodes if n.node_type == "evidence"]
        analysis_nodes = [n for n in nodes if n.node_type == "analysis"]
        risk_nodes = [n for n in nodes if n.node_type == "risk"]
        decision_node = next((n for n in nodes if n.node_type == "decision"), None)
        outcome_node = next((n for n in nodes if n.node_type == "outcome"), None)
        
        # Trigger → Evidence connections
        if trigger_node:
            for evidence_node in evidence_nodes:
                edge = DecisionEdge(
                    source=trigger_node.node_id,
                    target=evidence_node.node_id,
                    relationship="triggered_collection",
                    strength=evidence_node.importance,
                    description=f"Trigger led to collection of {evidence_node.title.lower()}"
                )
                edges.append(edge)
        
        # Evidence → Analysis connections
        for evidence_node in evidence_nodes:
            for analysis_node in analysis_nodes:
                # Check if evidence influenced this analysis
                if self._evidence_influenced_analysis(evidence_node, analysis_node, decision_chain):
                    edge = DecisionEdge(
                        source=evidence_node.node_id,
                        target=analysis_node.node_id,
                        relationship="informed",
                        strength=min(evidence_node.confidence or 0.5, analysis_node.confidence or 0.5),
                        description=f"Evidence informed {analysis_node.agent}'s analysis"
                    )
                    edges.append(edge)
        
        # Analysis → Risk connections
        for analysis_node in analysis_nodes:
            for risk_node in risk_nodes:
                edge = DecisionEdge(
                    source=analysis_node.node_id,
                    target=risk_node.node_id,
                    relationship="identified_risk",
                    strength=risk_node.importance,
                    description=f"{analysis_node.agent} identified risk factor"
                )
                edges.append(edge)
        
        # Analysis → Decision connections
        if decision_node:
            for analysis_node in analysis_nodes:
                edge = DecisionEdge(
                    source=analysis_node.node_id,
                    target=decision_node.node_id,
                    relationship="contributed_to",
                    strength=analysis_node.confidence or 0.5,
                    description=f"{analysis_node.agent}'s analysis contributed to final decision"
                )
                edges.append(edge)
        
        # Risk → Decision connections
        if decision_node:
            for risk_node in risk_nodes:
                edge = DecisionEdge(
                    source=risk_node.node_id,
                    target=decision_node.node_id,
                    relationship="influenced",
                    strength=risk_node.importance,
                    description=f"Risk assessment influenced decision"
                )
                edges.append(edge)
        
        # Decision → Outcome connection
        if decision_node and outcome_node:
            edge = DecisionEdge(
                source=decision_node.node_id,
                target=outcome_node.node_id,
                relationship="resulted_in",
                strength=1.0,
                description="Decision implementation resulted in outcome"
            )
            edges.append(edge)
        
        return edges
    
    def _create_network_graph(self, nodes: List[DecisionNode], edges: List[DecisionEdge]) -> Dict[str, Any]:
        """Create network graph visualization data"""
        # Create NetworkX graph for layout
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node.node_id, **{
                'title': node.title,
                'type': node.node_type,
                'importance': node.importance
            })
        
        # Add edges
        for edge in edges:
            G.add_edge(edge.source, edge.target, weight=edge.strength)
        
        # Calculate layout
        pos = nx.spring_layout(G, k=3, iterations=50)
        
        # Prepare node data for Plotly
        node_trace_data = {
            'x': [],
            'y': [],
            'text': [],
            'customdata': [],
            'marker': {
                'size': [],
                'color': [],
                'colorscale': 'Viridis',
                'showscale': True,
                'colorbar': dict(title="Importance")
            }
        }
        
        # Node type colors
        type_colors = {
            'trigger': '#FF6B6B',
            'evidence': '#4ECDC4',
            'analysis': '#45B7D1',
            'risk': '#FFA07A',
            'decision': '#98D8C8',
            'outcome': '#F7DC6F'
        }
        
        for node in nodes:
            x, y = pos[node.node_id]
            node_trace_data['x'].append(x)
            node_trace_data['y'].append(y)
            node_trace_data['text'].append(node.title)
            node_trace_data['customdata'].append({
                'description': node.description,
                'agent': node.agent,
                'confidence': node.confidence,
                'timestamp': node.timestamp,
                'type': node.node_type
            })
            node_trace_data['marker']['size'].append(max(20, node.importance * 50))
            node_trace_data['marker']['color'].append(node.importance)
        
        # Prepare edge data for Plotly
        edge_traces = []
        for edge in edges:
            x0, y0 = pos[edge.source]
            x1, y1 = pos[edge.target]
            
            edge_trace = {
                'x': [x0, x1, None],
                'y': [y0, y1, None],
                'mode': 'lines',
                'line': {
                    'width': max(1, edge.strength * 5),
                    'color': f'rgba(128, 128, 128, {edge.strength})'
                },
                'hoverinfo': 'text',
                'text': edge.description
            }
            edge_traces.append(edge_trace)
        
        return {
            'nodes': node_trace_data,
            'edges': edge_traces,
            'layout': {
                'title': 'Decision Flow Network',
                'showlegend': False,
                'hovermode': 'closest',
                'margin': dict(b=20,l=5,r=5,t=40),
                'annotations': [
                    dict(
                        text="Node size indicates importance, color indicates confidence/relevance",
                        showarrow=False,
                        xref="paper", yref="paper",
                        x=0.005, y=-0.002,
                        xanchor='left', yanchor='bottom',
                        font=dict(size=12)
                    )
                ],
                'xaxis': dict(showgrid=False, zeroline=False, showticklabels=False),
                'yaxis': dict(showgrid=False, zeroline=False, showticklabels=False)
            }
        }
    
    def _create_decision_timeline(self, decision_chain: Dict[str, Any]) -> Dict[str, Any]:
        """Create timeline visualization of decision process"""
        timeline_events = []
        
        # Add trigger event
        timeline_events.append({
            'date': decision_chain.get('created_at', ''),
            'event': 'Decision Triggered',
            'description': decision_chain.get('triggering_event', ''),
            'type': 'trigger',
            'agent': 'System'
        })
        
        # Add agent analyses
        for analysis in decision_chain.get('agent_analyses', []):
            timeline_events.append({
                'date': analysis.get('timestamp', ''),
                'event': f"Analysis by {analysis.get('agent_name', 'Unknown')}",
                'description': f"{analysis.get('analysis_type', '')}: {', '.join(analysis.get('key_findings', [])[:1])}",
                'type': 'analysis',
                'agent': analysis.get('agent_name', ''),
                'confidence': analysis.get('confidence_level', 0.5)
            })
        
        # Add final decision
        if decision_chain.get('decision_timestamp'):
            timeline_events.append({
                'date': decision_chain.get('decision_timestamp', ''),
                'event': 'Final Decision Made',
                'description': decision_chain.get('final_decision', ''),
                'type': 'decision',
                'agent': decision_chain.get('decision_maker', '')
            })
        
        # Add outcome if available
        if decision_chain.get('outcome_summary'):
            timeline_events.append({
                'date': decision_chain.get('updated_at', ''),
                'event': 'Outcome Recorded',
                'description': decision_chain.get('outcome_summary', ''),
                'type': 'outcome',
                'agent': 'System'
            })
        
        # Sort by date
        timeline_events.sort(key=lambda x: x['date'])
        
        return {
            'events': timeline_events,
            'duration': self._calculate_decision_duration(timeline_events)
        }
    
    def _create_confidence_flow(self, decision_chain: Dict[str, Any]) -> Dict[str, Any]:
        """Create confidence flow visualization"""
        confidence_data = []
        
        for i, analysis in enumerate(decision_chain.get('agent_analyses', [])):
            confidence_data.append({
                'agent': analysis.get('agent_name', 'Unknown'),
                'analysis_type': analysis.get('analysis_type', ''),
                'confidence': analysis.get('confidence_level', 0.5),
                'recommendations_count': len(analysis.get('recommendations', [])),
                'concerns_count': len(analysis.get('concerns', [])),
                'timestamp': analysis.get('timestamp', '')
            })
        
        return {
            'confidence_data': confidence_data,
            'avg_confidence': sum(item['confidence'] for item in confidence_data) / len(confidence_data) if confidence_data else 0,
            'confidence_variance': self._calculate_confidence_variance(confidence_data)
        }
    
    def _create_decision_summary(self, decision_chain: Dict[str, Any]) -> Dict[str, Any]:
        """Create decision summary with key metrics"""
        agent_analyses = decision_chain.get('agent_analyses', [])
        
        return {
            'decision_id': decision_chain.get('decision_id', ''),
            'priority': decision_chain.get('priority', 'Medium'),
            'status': decision_chain.get('status', 'Unknown'),
            'agents_involved': list(set(analysis.get('agent_name', '') for analysis in agent_analyses)),
            'evidence_count': len(decision_chain.get('evidence_considered', [])),
            'risk_factors_count': len(decision_chain.get('risk_assessments', [])),
            'avg_confidence': sum(analysis.get('confidence_level', 0) for analysis in agent_analyses) / len(agent_analyses) if agent_analyses else 0,
            'implementation_status': decision_chain.get('implementation_status', 'Unknown'),
            'follow_up_required': decision_chain.get('follow_up_required', False),
            'created_at': decision_chain.get('created_at', ''),
            'decision_timestamp': decision_chain.get('decision_timestamp', ''),
            'updated_at': decision_chain.get('updated_at', '')
        }
    
    # Helper methods
    def _calculate_risk_importance(self, risk: Dict[str, Any]) -> float:
        """Calculate importance score for risk assessment"""
        risk_level_scores = {
            'Low': 0.2,
            'Medium': 0.5,
            'High': 0.8,
            'Critical': 1.0
        }
        
        impact_scores = {
            'Low': 0.2,
            'Medium': 0.5,
            'High': 0.8,
            'Critical': 1.0
        }
        
        risk_score = risk_level_scores.get(risk.get('risk_level', 'Medium'), 0.5)
        impact_score = impact_scores.get(risk.get('impact_severity', 'Medium'), 0.5)
        probability = risk.get('probability', 0.5)
        
        return (risk_score + impact_score + probability) / 3
    
    def _evidence_influenced_analysis(self, evidence_node: DecisionNode, analysis_node: DecisionNode, decision_chain: Dict[str, Any]) -> bool:
        """Check if evidence influenced a specific analysis"""
        # Simple heuristic: evidence influences analysis if they're close in time or related to same agent
        if evidence_node.agent == analysis_node.agent:
            return True
        
        # Check temporal proximity (within reasonable time window)
        try:
            evidence_time = datetime.fromisoformat(evidence_node.timestamp)
            analysis_time = datetime.fromisoformat(analysis_node.timestamp)
            time_diff = abs((analysis_time - evidence_time).total_seconds() / 3600)  # hours
            return time_diff < 24  # Within 24 hours
        except:
            return True  # Default to connected if can't determine timing
    
    def _calculate_decision_duration(self, timeline_events: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate decision process duration"""
        if len(timeline_events) < 2:
            return {"total_hours": 0, "phases": []}
        
        try:
            start_time = datetime.fromisoformat(timeline_events[0]['date'])
            end_time = datetime.fromisoformat(timeline_events[-1]['date'])
            total_hours = (end_time - start_time).total_seconds() / 3600
            
            phases = []
            for i in range(len(timeline_events) - 1):
                phase_start = datetime.fromisoformat(timeline_events[i]['date'])
                phase_end = datetime.fromisoformat(timeline_events[i + 1]['date'])
                phase_duration = (phase_end - phase_start).total_seconds() / 3600
                
                phases.append({
                    'from': timeline_events[i]['event'],
                    'to': timeline_events[i + 1]['event'],
                    'duration_hours': phase_duration
                })
            
            return {
                "total_hours": total_hours,
                "phases": phases
            }
        except:
            return {"total_hours": 0, "phases": []}
    
    def _calculate_confidence_variance(self, confidence_data: List[Dict[str, Any]]) -> float:
        """Calculate variance in confidence levels"""
        if not confidence_data:
            return 0
        
        confidences = [item['confidence'] for item in confidence_data]
        mean_confidence = sum(confidences) / len(confidences)
        variance = sum((c - mean_confidence) ** 2 for c in confidences) / len(confidences)
        
        return variance

    def create_decision_comparison(self, decision_chains: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create comparison visualization between multiple decisions"""
        comparison_data = []
        
        for chain in decision_chains:
            analyses = chain.get('agent_analyses', [])
            
            comparison_data.append({
                'decision_id': chain.get('decision_id', ''),
                'priority': chain.get('priority', 'Medium'),
                'agents_count': len(set(a.get('agent_name', '') for a in analyses)),
                'avg_confidence': sum(a.get('confidence_level', 0) for a in analyses) / len(analyses) if analyses else 0,
                'evidence_count': len(chain.get('evidence_considered', [])),
                'risk_count': len(chain.get('risk_assessments', [])),
                'implementation_status': chain.get('implementation_status', 'Unknown'),
                'created_at': chain.get('created_at', ''),
                'final_decision': chain.get('final_decision', '')[:50] + "..." if len(chain.get('final_decision', '')) > 50 else chain.get('final_decision', '')
            })
        
        return {
            'comparison_data': comparison_data,
            'insights': self._generate_comparison_insights(comparison_data)
        }
    
    def _generate_comparison_insights(self, comparison_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate insights from decision comparison"""
        if not comparison_data:
            return {}
        
        avg_confidence = sum(d['avg_confidence'] for d in comparison_data) / len(comparison_data)
        avg_agents = sum(d['agents_count'] for d in comparison_data) / len(comparison_data)
        
        high_confidence_decisions = [d for d in comparison_data if d['avg_confidence'] > 0.8]
        complex_decisions = [d for d in comparison_data if d['agents_count'] > 2]
        
        return {
            'total_decisions': len(comparison_data),
            'avg_confidence_across_all': avg_confidence,
            'avg_agents_per_decision': avg_agents,
            'high_confidence_count': len(high_confidence_decisions),
            'complex_decisions_count': len(complex_decisions),
            'most_confident_decision': max(comparison_data, key=lambda x: x['avg_confidence'])['decision_id'] if comparison_data else None,
            'most_complex_decision': max(comparison_data, key=lambda x: x['agents_count'])['decision_id'] if comparison_data else None
        }
