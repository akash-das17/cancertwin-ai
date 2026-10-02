# CancerTwin AI — Agentic Digital Twin for Personalized Cancer Risk & What-If Simulation

CancerTwin AI is an agentic clinical digital twin platform that couples personalized risk modeling with counterfactual "What-If" intervention simulation, evidence-grounded by a local **ChromaDB** vector store and a lightweight multi-agent orchestration architecture.

---

## Architecture Overview

```
                          ┌──────────────────────────┐
                          │   Clinician / Patient    │
                          └────────────┬─────────────┘
                                       │
                                       ▼
                          ┌──────────────────────────┐
                          │   FastAPI Web & REST     │
                          │   Interactive Dashboard  │
                          └────────────┬─────────────┘
                                       │
                ┌──────────────────────┴──────────────────────┐
                │        Twin Coordinator Agent               │
                └───────┬──────────────┬──────────────┬───────┘
                        │              │              │
      ┌─────────────────▼──┐    ┌──────▼──────┐   ┌───▼────────────────┐
      │ Intake & Profiler  │    │ Risk Agent  │   │ What-If Simulator  │
      │ Agent              │    │ (RAG-Driven)│   │ Agent              │
      └────────────────────┘    └──────┬──────┘   └───┬────────────────┘
                                       │              │
                                ┌──────▼──────────────▼───────┐
                                │     ChromaDB Vector Store   │
                                │   (USPSTF, NCCN Guidelines) │
                                └─────────────────────────────┘
```

### 1. Simple Multi-Agent System (`src/agents/`)
- **Intake & Profiler Agent (`intake_agent.py`)**: Ingests raw patient clinical parameters (age, biological sex, genetic mutations like BRCA/Lynch, smoking pack-years, BMI, alcohol, exercise), validates inputs, and constructs the normalized `DigitalTwinState`.
- **Clinical Risk Assessment Agent (`risk_agent.py`)**: Uses empirical risk models (Gail, Bach/USPSTF, WCRF) and queries ChromaDB for evidence-based hazard ratios across multi-cancer axes (Lung, Colorectal, Breast).
- **What-If Simulation Agent (`simulation_agent.py`)**: Evaluates actionable lifestyle and screening counterfactuals (e.g. smoking cessation, targeted weight loss, adherence to colonoscopy/LDCT screening) and computes risk reduction deltas and 10-year divergent trajectory curves.
- **Twin Coordinator Agent (`coordinator.py`)**: Orchestrates the multi-agent pipeline, enforces deterministic data flow, and generates an explainable clinical summary with step-by-step reasoning traces.

### 2. Evidence RAG Layer with ChromaDB (`src/rag/`)
- **Persistent Vector Store (`vector_store.py`)**: Connects to ChromaDB (`PersistentClient`), managing guideline embeddings and metadata filtering (`cancer_type`, `evidence_level`, `hazard_ratio`). Includes resilient fallback support.
- **Guideline Ingestion (`ingest.py`)**: Parses and embeds clinical oncology guidelines from USPSTF, NCCN, and WCRF stored in `data/raw_guidelines/`.
- **Oncology Retriever (`retriever.py`)**: Specialized semantic search functions for risk factors and counterfactual intervention evidence.

### 3. Interactive Web Dashboard (`web/`)
- **Digital Twin Profile Card**: Real-time health index score and vulnerability tags.
- **Dynamic What-If Sliders**: Interactive controls for smoking cessation, target BMI, exercise hours, and screening adherence.
- **Visual Trajectory Chart**: Canvas-based 10-year cumulative risk curve comparing Baseline vs. Counterfactual scenarios.
- **Live Agent Reasoning Trace & ChromaDB Citations**: Inspectable audit trail of each agent's decisions and guideline sources.

---

## Project File Structure

```
CancerTwin-AI/
├── .env.example                          # Environment template (ChromaDB paths, LLM keys)
├── requirements.txt                      # Python dependencies (fastapi, chromadb, etc.)
├── README.md                             # Project documentation & architecture
│
├── data/                                 # Data & Local Vector Database
│   ├── raw_guidelines/                   # Clinical guideline JSON records
│   │   ├── lung_cancer_uspstf.json
│   │   ├── colorectal_lifestyle.json
│   │   └── breast_cancer_gail_factors.json
│   └── chromadb/                         # Persistent ChromaDB vector storage directory
│
├── src/                                  # Application Source Code
│   ├── __init__.py
│   ├── config.py                         # App configuration and paths
│   │
│   ├── models/                           # Pydantic Data Models
│   │   ├── __init__.py
│   │   ├── patient.py                    # PatientProfile & DigitalTwinState
│   │   ├── simulation.py                 # WhatIfScenario & InterventionParameters
│   │   └── risk_report.py                # RiskReport, GuidelineEvidence, AgentTraceLog
│   │
│   ├── rag/                              # ChromaDB Vector Store & Ingestion
│   │   ├── __init__.py
│   │   ├── vector_store.py               # ChromaDB client & collection manager
│   │   ├── ingest.py                     # Guideline embedding & ingestion script
│   │   └── retriever.py                  # Semantic query interface for agents
│   │
│   ├── agents/                           # Simple Multi-Agent System
│   │   ├── __init__.py
│   │   ├── base.py                       # BaseAgent abstract class & trace logger
│   │   ├── coordinator.py                # TwinCoordinatorAgent orchestrator
│   │   ├── intake_agent.py               # Ingestion & twin state normalization
│   │   ├── risk_agent.py                 # Multi-cancer risk calculation & RAG retrieval
│   │   └── simulation_agent.py           # Counterfactual trajectory generator
│   │
│   ├── utils/                            # Algorithms & Prompts
│   │   ├── __init__.py
│   │   ├── risk_calculators.py           # Parametric risk formulas (Lung, Colorectal, Breast)
│   │   └── prompts.py                    # Clinical narrative synthesis
│   │
│   └── api/                              # REST API
│       ├── __init__.py
│       └── app.py                        # FastAPI endpoints (/twin/simulate, /rag/search, etc.)
│
└── web/                                  # Modern Web Dashboard
    ├── index.html                        # Sleek dark-mode interface
    ├── styles.css                        # Glassmorphism & medical UI styling
    └── app.js                            # Interactive client & canvas chart rendering
```

---

## Getting Started

### 1. Prerequisites & Installation
Ensure Python 3.10+ is installed:
```bash
py -m pip install -r requirements.txt
```

### 2. Ingest Guidelines into ChromaDB
Seed the local ChromaDB vector store with clinical oncology guidelines:
```bash
py -m src.rag.ingest
```

### 3. Run the Application
Launch the FastAPI server:
```bash
py -m uvicorn src.api.app:app --reload --port 8000
```
Open your browser and navigate to:
**`http://localhost:8000`**

---

## API Endpoints

- `GET /api/health` — Status and configuration health check.
- `POST /api/twin/profile` — Ingests a `PatientProfile` and returns an initialized `DigitalTwinState`.
- `POST /api/twin/simulate` — Executes the full multi-agent pipeline (`IntakeAgent` $\rightarrow$ `RiskAssessmentAgent` $\rightarrow$ `WhatIfSimulatorAgent` $\rightarrow$ `TwinCoordinatorAgent`) and outputs a full `RiskReport`.
- `GET /api/rag/search` — Query the ChromaDB oncology vector store with optional `cancer_type` filtering.
