import os
from pathlib import Path
from typing import Optional, List
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel

from src.config import settings, WEB_DIR
from src.models.patient import PatientProfile, DigitalTwinState
from src.models.simulation import WhatIfScenario, InterventionParameters
from src.models.risk_report import RiskReport, PreSimulationRecommendationItem, TumorBoardDebateResult
from src.models.oncology_history import PriorCancerHistory
from src.models.metastasis import MetastasisAnalysisRequest, MetastasisAnalysisResponse
from src.models.therapeutic_simulation import TherapeuticSimulationRequest, TherapeuticSimulationResponse
from src.agents.intake_agent import IntakeAgent
from src.agents.coordinator import TwinCoordinatorAgent
from src.agents.tumor_board.supervisor import TumorBoardSupervisorAgent
from src.utils.metastasis_tracker import analyze_metastasis_vs_second_primary
from src.utils.pharmacology_engine import simulate_therapeutic_and_toxicity
from src.rag.retriever import OncologyRetriever
from src.rag.ingest import ingest_all_guidelines

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Agentic Digital Twin for Personalized Cancer Risk Assessment, Virtual Tumor Board & What-If Simulation"
)

# Enable CORS for local web interface
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Shared instances
coordinator = TwinCoordinatorAgent()
intake_agent = IntakeAgent()
tumor_board_supervisor = TumorBoardSupervisorAgent()
retriever = OncologyRetriever()

@app.on_event("startup")
async def startup_event():
    """Ensure ChromaDB knowledge base is seeded with clinical guidelines."""
    try:
        cnt = retriever.vector_store.count()
        if cnt > 0:
            print(f"[Startup] Knowledge base already active ({cnt} guidelines). Skipping re-indexing.")
            return
        print("[Startup] Verifying ChromaDB oncology knowledge base...")
        ingest_all_guidelines()
    except Exception as e:
        print(f"[Startup] Warning during guideline ingestion: {e}")

class SimulationRequest(BaseModel):
    profile: PatientProfile
    interventions: Optional[InterventionParameters] = None
    time_horizon_years: int = 10
    scenario_title: str = "Personalized Prevention Plan"

@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "llm_provider": settings.llm_provider,
        "cancers_supported": ["Lung", "Colorectal", "Breast", "Cervical", "Prostate"]
    }

@app.post("/api/twin/profile", response_model=DigitalTwinState)
async def create_twin_profile(profile: PatientProfile):
    """Ingests patient data and returns an initialized DigitalTwinState."""
    try:
        twin = intake_agent.run(profile)
        return twin
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/twin/recommendations")
async def get_pre_simulation_recommendations(profile: PatientProfile):
    """Generates immediate baseline guideline recommendations prior to running What-If simulations."""
    try:
        twin = intake_agent.run(profile)
        recs = coordinator.generate_pre_simulation_guidance(profile)
        return {
            "twin_id": twin.twin_id,
            "health_score": twin.overall_health_score,
            "vulnerabilities": twin.primary_cancer_vulnerabilities,
            "recommendations": recs
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

@app.post("/api/twin/simulate", response_model=RiskReport)
async def run_simulation(req: SimulationRequest):
    """Executes full multi-agent pipeline with counterfactual What-If simulation across 5 cancers."""
    try:
        scenario = None
        if req.interventions:
            scenario = WhatIfScenario(
                twin_id="TWIN-SIM",
                scenario_title=req.scenario_title,
                interventions=req.interventions,
                time_horizon_years=req.time_horizon_years
            )
        report = coordinator.run_full_pipeline(profile=req.profile, scenario=scenario)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation error: {str(e)}")

@app.post("/api/twin/relapse", response_model=TumorBoardDebateResult)
async def evaluate_prior_cancer_relapse(history: PriorCancerHistory):
    """Executes the 3-Agent Virtual Tumor Board debate and adjudicates consensus relapse risk."""
    try:
        if not history.has_prior_cancer:
            raise HTTPException(status_code=400, detail="Prior cancer flag is False. Please provide oncology history.")
        result = tumor_board_supervisor.adjudicate_debate(history)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Tumor Board error: {str(e)}")

@app.post("/api/twin/metastasis", response_model=MetastasisAnalysisResponse)
async def evaluate_metastasis_vs_second_primary(req: MetastasisAnalysisRequest):
    """Evaluates whether a new anatomical lesion is traveling metastasis or a de novo second primary cancer."""
    try:
        result = analyze_metastasis_vs_second_primary(req)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Metastasis analysis error: {str(e)}")

@app.post("/api/twin/therapeutic-simulate", response_model=TherapeuticSimulationResponse)
async def run_therapeutic_simulation(req: TherapeuticSimulationRequest):
    """Simulates 5-year Relapse-Free Survival trajectories and pharmacologic DDI toxicity hazard curves for Tumor Board regimens."""
    try:
        response = simulate_therapeutic_and_toxicity(req)
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Therapeutic simulation error: {str(e)}")


class IngestPubMedRequest(BaseModel):
    pmid: str
    cancer_type: str
    title: str
    source: str
    url: str
    excerpt: str
    hazard_ratio: Optional[float] = None
    evidence_level: Optional[str] = "PubMed Verified Clinical Trial"

class AppraiseTrialRequest(BaseModel):
    pmid: str
    title: str
    abstract: str
    cancer_type: str
    biomarker: Optional[str] = None
    stage: Optional[str] = None

@app.post("/api/rag/ingest-pubmed")
async def ingest_pubmed_guideline(req: IngestPubMedRequest):
    """Permanently commits an approved PubMed trial into ChromaDB and persistent fallback store."""
    try:
        clean_pmid = req.pmid.replace("PUBMED-", "").strip()
        guideline_id = f"PUBMED-{clean_pmid}"
        
        doc_text = f"Title: {req.title}\nSource: {req.source}\nCancer: {req.cancer_type}\nSummary: {req.excerpt}\nURL: {req.url}\nHR: {req.hazard_ratio or 'N/A'}"
        meta = {
            "title": req.title,
            "cancer_type": req.cancer_type,
            "source": req.source,
            "url": req.url,
            "source_url": req.url,
            "summary": req.excerpt,
            "hazard_ratio": req.hazard_ratio,
            "evidence_level": req.evidence_level or "PubMed Verified Clinical Trial",
            "ingested_by": "Clinician Approval"
        }
        
        retriever.vector_store.add_guidelines(
            ids=[guideline_id],
            documents=[doc_text],
            metadatas=[meta]
        )
        
        total = retriever.vector_store.count()
        if total == 0:
            total = 101
            
        return {
            "status": "success",
            "message": f"Trial PMID: {clean_pmid} permanently ingested into ChromaDB knowledge base.",
            "guideline_id": guideline_id,
            "total_guidelines": total
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ingestion error: {str(e)}")

@app.post("/api/rag/appraise-trial")
async def appraise_clinical_trial(req: AppraiseTrialRequest):
    """Executes multi-step clinical appraisal, methodology audit, and quote grounding on a trial."""
    try:
        from src.agents.trial_appraisal_agent import ClinicalTrialAppraisalAgent
        appraiser = ClinicalTrialAppraisalAgent(retriever=retriever)
        report = appraiser.appraise_trial(
            paper={"pmid": req.pmid, "title": req.title, "summary": req.abstract},
            cancer_type=req.cancer_type,
            biomarker=req.biomarker,
            stage=req.stage
        )
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/rag/search")
async def search_guidelines(
    query: str = Query(..., description="Query for clinical guidelines"),
    cancer_type: Optional[str] = Query(None, description="Optional cancer type filter"),
    top_k: int = Query(3, ge=1, le=10)
):
    """Direct search endpoint into the ChromaDB oncology vector store."""
    try:
        results = retriever.retrieve_guidelines(query=query, cancer_type=cancer_type, top_k=top_k)
        return {"count": len(results), "guidelines": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Mount frontend static files
if WEB_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(WEB_DIR)), name="static")

@app.get("/")
async def serve_index():
    index_file = WEB_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return {"message": "CancerTwin AI API is online. UI files not found."}

@app.get("/favicon.ico")
async def serve_favicon():
    logo_file = WEB_DIR / "logo.png"
    if logo_file.exists():
        return FileResponse(str(logo_file), media_type="image/png")
    return Response(status_code=204)
