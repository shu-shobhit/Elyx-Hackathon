# Elyx Event System - Member Journey Simulation & Visualization

This system simulates healthcare conversations between AI agents and members, then provides comprehensive visualization of the journey data.

## 🏗️ System Overview

The system consists of two main components:
1. **Message Generation**: AI agents simulate healthcare conversations week by week
2. **Visualization Dashboard**: Interactive analysis of member journeys, decisions, and agent performance

## 📋 Prerequisites

- Python 3.8+
- Required packages (install via `pip install -r requirements.txt`):
  - streamlit
  - plotly
  - pandas
  - langchain
  - groq (for LLM access)

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Set Up Environment
- Ensure you have access to Groq API (or modify `utils.py` for your preferred LLM)
- The system will create necessary directories automatically

## 💬 Message Generation

### Running the Simulation

The main simulation script generates conversations between AI agents and members over multiple weeks.

#### Basic Usage
```bash
cd elyx_event_system
python main.py
```

#### Command Line Options
```bash
# Run automatically for 35 weeks
python main.py --auto

# Resume from a specific week
python main.py --resume 5

# Limit to specific number of weeks
python main.py --max-weeks 10

# Combine options
python main.py --auto --resume 3 --max-weeks 20
```

#### What Happens During Generation
1. **Weekly Simulation**: Each week generates 2-4 conversation threads
2. **Agent Interactions**: Ruby (coordinator), Dr. Warren (medical), Carla (nutrition), Advik (data), Rachel (coaching), Neel (specialist), TestPanel (diagnostics)
3. **State Persistence**: Weekly checkpoints saved to `checkpoints/` directory
4. **Chat History**: Complete conversations saved as text files with timestamps

#### Output Files
- `checkpoints/week_XX_checkpoint.json` - Complete state for each week
- `checkpoints/week_XX_chat_history.txt` - Human-readable conversation logs
- `final_complete_chat_history.txt` - Complete journey summary

## 📊 Visualization Dashboard

### Running the Dashboard

The enhanced dashboard provides comprehensive analysis of the generated data.

#### Launch Dashboard
```bash
cd elyx_event_system
streamlit run enhanced_dashboard.py
```

#### Dashboard Features

##### 1. **Overview** 📊
- Key metrics and episode distribution
- Episode types and trigger analysis
- High-level journey insights

##### 2. **Episodes & Recommendations** 📋
- **State-change based episodes** (not just conversations)
- **Actual recommendations** provided by agents
- **Medications and tests** prescribed
- **Decision IDs** for full traceability

##### 3. **Decision Backtracking** 🔄
- **Decision tree visualization** using decision IDs
- **Agent collaboration flows** and analysis chains
- **Evidence and reasoning** for each decision
- **Decision outcome tracking** and rationale

##### 4. **Agent Time Analysis** ⏱️
- **Detailed time estimation** based on activities:
  - Base response time: 8 minutes
  - Complexity factors: 3 min per 100 characters
  - Recommendation time: 6 min per recommendation
  - Medication review: 12 min per medication
  - Test analysis: 10 min per test
  - Expert coordination: 8 min per consultation
- **Weekly time trends** per agent
- **Efficiency metrics** (recommendations/hour)
- **Activity breakdowns** by agent

##### 5. **Detailed Insights** 🔬
- Decision effectiveness correlations
- Recommendation pattern analysis
- Agent performance statistics

## 🔧 Configuration

### Agent Behavior
- Modify `prompts.py` to adjust agent personalities and response patterns
- Update `state.py` to modify data structures
- Adjust `orchestrator.py` for conversation flow logic

### Simulation Parameters
- **Weeks**: Default 35 weeks (modify in `main.py`)
- **Threads per week**: Random 2-4 (modify in `main.py`)
- **Checkpointing**: Automatic weekly saves

## 📁 File Structure

```
elyx_event_system/
├── main.py                 # Main simulation script
├── enhanced_dashboard.py   # Main visualization dashboard
├── journey_analyzer.py     # Data analysis engine
├── decision_visualizer.py  # Decision tree visualization
├── state.py               # Data structures and types
├── prompts.py             # Agent system prompts
├── orchestrator.py        # Conversation flow logic
├── utils.py               # Utility functions
├── agents/                # Individual agent implementations
│   ├── ruby.py           # Coordinator agent
│   ├── dr_warren.py      # Medical strategist
│   ├── carla.py          # Nutritionist
│   ├── advik.py          # Data analyst
│   ├── rachel.py         # Health coach
│   ├── neel.py           # Specialist
│   ├── test_panel.py     # Diagnostic testing
│   └── member.py         # Member simulation
├── checkpoints/           # Generated data (created automatically)
└── requirements.txt       # Python dependencies
```

## 🚨 Troubleshooting

### Common Issues

#### Message Generation Fails
- Check API key configuration in `utils.py`
- Verify all required packages are installed
- Ensure sufficient disk space for checkpoints

#### Dashboard Won't Load
- Verify checkpoint files exist in `checkpoints/` directory
- Check Streamlit installation: `pip install streamlit`
- Restart Streamlit if session state issues occur

#### No Episodes Found
- Ensure message generation completed successfully
- Check checkpoint file format and content
- Verify `journey_analyzer.py` can parse the data

### Performance Tips
- **Large datasets**: Use week range filters in dashboard
- **Memory issues**: Process data in smaller batches
- **Slow loading**: Pre-generate analysis data

## 🔄 Workflow Example

### Complete End-to-End Process

1. **Generate Data**
   ```bash
   cd elyx_event_system
   python main.py --auto --max-weeks 10
   ```

2. **Launch Dashboard**
   ```bash
   streamlit run enhanced_dashboard.py
   ```

3. **Analyze Results**
   - Load data via sidebar
   - Explore episodes and recommendations
   - Track decision evolution
   - Analyze agent performance

4. **Export Insights**
   - Screenshot visualizations
   - Copy key metrics
   - Download episode data

## 📈 Customization

### Adding New Agents
1. Create agent file in `agents/` directory
2. Implement required functions
3. Add to `agents/__init__.py`
4. Update `orchestrator.py` routing logic

### Modifying Data Structures
1. Update `state.py` with new fields
2. Modify `journey_analyzer.py` to extract new data
3. Update dashboard to visualize new metrics

### Changing Simulation Logic
1. Modify `orchestrator.py` for conversation flow
2. Update `prompts.py` for agent behavior
3. Adjust `main.py` for simulation parameters
