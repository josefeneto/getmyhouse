# 🏠 GetMyHouse - AI-Powered Property Search System

**Capstone Project for "5-Day AI Agents Intensive with Google ADK"**

## 🎯 Project Overview

GetMyHouse is a multi-agent AI system built with Google's Agent Development Kit (ADK) that helps users find residential properties in Portugal. The system demonstrates advanced agentic architectures including multi-agent coordination, MCP tool integration, session memory, and production deployment.

## 🏗️ Architecture

### Multi-Agent System
```
ROOT AGENT (Coordinator)
├── PARALLEL AGENT (Search Phase)
│   ├── Property Search Agent (MCP Tools)
│   └── Mock Data Tool (MVP Phase)
└── SEQUENTIAL AGENT (Processing Phase)
    ├── Filter & Ranking Agent
    └── Report Generator Agent
```

### Key Components

**1. Coordinator Agent (LlmAgent)**
- Orchestrates the entire workflow
- Manages user interactions via Streamlit UI
- Coordinates specialized agents using AgentTool pattern
- Handles session state and memory

**2. Search Agent (Specialist)**
- Uses MCP tools for property search
- Integrates with Portuguese real estate portals (Idealista, Imovirtual)
- Falls back to mock data during MVP phase
- Implements retry logic and error handling

**3. Filter Agent (Specialist)**
- Ranks properties based on user requirements
- Calculates match scores (0-1 scale)
- Applies business logic for property relevance
- Returns top 10 properties

**4. Report Agent (Specialist)**
- Generates structured output (table format)
- Creates Excel export functionality
- Includes verified property links
- Provides summary statistics

## 🛠️ Technical Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Framework** | Google ADK (Python) | Multi-agent orchestration |
| **LLM** | Gemini 2.0 Flash | Agent reasoning engine |
| **UI** | Streamlit | User interface |
| **Database** | SQLite | Session & memory persistence |
| **Deployment** | Docker + Railway | Production hosting |
| **Observability** | Python logging + ADK tracing | Monitoring & debugging |

## 🎓 ADK Concepts Demonstrated

### Day 1: Agent Architectures
- ✅ LlmAgent for dynamic reasoning
- ✅ Workflow agents (ParallelAgent, SequentialAgent)
- ✅ Custom agent tools
- ✅ Think-Act-Observe loop

### Day 2: Tools & MCP
- ✅ Custom tool functions
- ✅ MCP tool integration (structured)
- ✅ Tool error handling & validation
- ✅ Tool documentation & schemas

### Day 3: Sessions & Memory
- ✅ Session state management (SQLite)
- ✅ User preference persistence
- ✅ Search refinement capability
- ✅ Conversation history

### Day 4: Observability & Evaluation
- ✅ Structured logging (DEBUG/INFO/ERROR)
- ✅ ADK event tracing
- ✅ Agent evaluation dataset
- ✅ Unit tests for agents

### Day 5: Production Deployment
- ✅ Docker containerization
- ✅ Railway cloud deployment
- ✅ Environment configuration
- ✅ Health checks & monitoring

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- Google Cloud API Key (Gemini)
- Docker (optional)

### Local Development

```bash
# Clone repository
git clone https://github.com/yourusername/getmyhouse.git
cd getmyhouse

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env and add your GOOGLE_API_KEY

# Run application
streamlit run app.py
```

### Docker Deployment

```bash
# Build image
docker build -t getmyhouse:latest .

# Run container
docker run -p 8501:8501 --env-file .env getmyhouse:latest
```

### Railway Deployment

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Initialize project
railway init

# Deploy
railway up
```

## 📝 User Guide

### Search Parameters

| Parameter | Options | Default |
|-----------|---------|---------|
| **Country** | Portugal, Spain, etc. | Portugal |
| **Location** | Free text (city/area) | - |
| **Distance** | 1, 2, 5, 10, 20 km, any | 1 km |
| **Property Type** | house, flat | - |
| **Typology** | T0, T1, T2, T3, T4+ | - |
| **WCs** | 1, 2, 3, any | any |
| **Usage State** | brand new, new (<5y), used, recovery | - |
| **Price Range** | Min-Max (EUR) | - |
| **Public Transport** | 5, 15, 30 min, any | any |
| **Other Requirements** | Free text | - |

### Search Refinement

The system remembers your previous searches and allows refinement:
1. Perform initial search
2. Review results
3. Click "Refine Search" 
4. Adjust parameters (previous values pre-filled)
5. Execute refined search

### Output Format

Results are displayed as a table with:
- All requirement attributes
- Price (EUR)
- Agency name
- Verified property link
- Match score (relevance)

Export to Excel available via download button.

## 🧪 Testing

### Run Unit Tests
```bash
pytest tests/ -v
```

### Run Agent Evaluation
```bash
python -m src.evaluation.run_evaluation
```

### Manual Testing (Dev UI)
```bash
adk dev ui --agent src.agents.coordinator
```

## 📊 Project Structure

```
getmyhouse/
├── src/
│   ├── agents/
│   │   ├── __init__.py
│   │   ├── coordinator.py      # Root coordinator agent
│   │   ├── search_agent.py     # Property search specialist
│   │   ├── filter_agent.py     # Filtering & ranking specialist
│   │   └── report_agent.py     # Report generation specialist
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── mock_search_tool.py # Mock data provider (MVP)
│   │   ├── web_scraper_tool.py # Real scraper (if implemented)
│   │   └── excel_export_tool.py # Excel generation
│   ├── memory/
│   │   ├── __init__.py
│   │   └── session_manager.py  # SQLite session persistence
│   ├── evaluation/
│   │   ├── __init__.py
│   │   ├── test_dataset.py     # Multi-turn test cases
│   │   └── run_evaluation.py   # Evaluation runner
│   ├── config.py               # Configuration constants
│   └── utils.py                # Utility functions
├── tests/
│   ├── test_agents.py
│   ├── test_tools.py
│   └── test_session.py
├── app.py                       # Streamlit UI
├── requirements.txt
├── Dockerfile
├── railway.json
├── .env.example
├── .gitignore
└── README.md
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file:

```bash
# Google Cloud
GOOGLE_API_KEY=your_gemini_api_key_here

# Application
APP_ENV=development  # development | production
LOG_LEVEL=INFO       # DEBUG | INFO | WARNING | ERROR

# Database
DB_PATH=./data/sessions.db

# Streamlit (Railway)
PORT=8501
```

## 📈 Development Roadmap

### Phase 1: MVP (Days 1-3) ✅
- [x] Multi-agent architecture
- [x] Mock data search tool
- [x] Basic Streamlit UI
- [x] Session memory (SQLite)
- [x] Logging & observability

### Phase 2: Real Data (Days 4-5)
- [ ] Web scraper for Idealista
- [ ] Web scraper for Imovirtual
- [ ] Error handling & fallbacks
- [ ] Rate limiting

### Phase 3: Production (Day 5)
- [ ] Docker containerization
- [ ] Railway deployment
- [ ] CI/CD pipeline
- [ ] Documentation finalization

### Future Enhancements
- [ ] Internationalization (i18n)
- [ ] User authentication
- [ ] A2A protocol implementation
- [ ] Advanced filtering algorithms
- [ ] Property image analysis

## 🤝 Contributing

This is a capstone project for educational purposes. However, feedback and suggestions are welcome:

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Open a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👤 Author

**José Neto**
- Course: 5-Day AI Agents Intensive with Google ADK
- Date: November 2024
- GitHub: [@josefeneto](https://github.com/josefeneto)

## 🙏 Acknowledgments

- Google AI Team for the Agent Development Kit
- Kaggle for hosting the 5-Day AI Agents Intensive course
- Portuguese real estate platforms (Idealista, Imovirtual)

## 📞 Support

For issues or questions about this project:
1. Check the [GitHub Issues](https://github.com/yourusername/getmyhouse/issues)
2. Review ADK documentation: https://google.github.io/adk-docs/
3. Contact via course forum

---

**Built with ❤️ using Google ADK | November 2024**
