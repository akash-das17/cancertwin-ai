from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime

class GuidelineEvidence(BaseModel):
    id: str
    cancer_type: str
    title: str
    source: str
    excerpt: str
    hazard_ratio: Optional[float] = None
    evidence_level: Optional[str] = None
    url: Optional[str] = None
    appraisal: Optional[Dict[str, Any]] = None

class RiskTrajectoryPoint(BaseModel):
    year: int
    baseline_risk_pct: float
    counterfactual_risk_pct: float

class CancerRiskAssessment(BaseModel):
    cancer_type: str  # e.g., "Lung", "Colorectal", "Breast", "Cervical", "Prostate"
    baseline_risk_pct: float = Field(ge=0.0, le=100.0)
    counterfactual_risk_pct: float = Field(ge=0.0, le=100.0)
    absolute_risk_reduction_pct: float
    relative_risk_reduction_pct: float
    population_average_pct: float
    risk_category: str  # "Low", "Moderate", "Elevated", "High"
    key_drivers: List[str]
    evidence_citations: List[GuidelineEvidence] = Field(default_factory=list)
    trajectory: List[RiskTrajectoryPoint] = Field(default_factory=list)

class AgentTraceLog(BaseModel):
    agent_name: str
    step_title: str
    details: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class PreSimulationRecommendationItem(BaseModel):
    category: str = Field(..., description="'Screening', 'Dietary', 'Lifestyle', 'Environmental', 'Genetic'")
    title: str
    recommendation: str
    guideline_source: str
    action_interval: str
    impact_estimate: str
    url: Optional[str] = None

class TumorBoardAgentOpinion(BaseModel):
    agent_role: str
    specialist_name: str
    assessed_relapse_risk_pct: float
    reasoning: str
    key_concerns: List[str]
    recommended_interventions: List[str]

class DebateMessage(BaseModel):
    round_number: int  # 1: Opening Position, 2: Cross-Rebuttal & Challenge, 3: Consensus Adjudication
    round_title: str
    speaker_role: str
    speaker_name: str
    target_peer: Optional[str] = None
    content: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class TumorBoardDebateResult(BaseModel):
    primary_cancer: str
    stage: str
    consensus_relapse_risk_5yr_pct: float
    risk_tier: str
    consensus_summary: str
    key_debate_points: List[str]
    adjudication_rationale: str
    agent_opinions: List[TumorBoardAgentOpinion]
    action_plan: List[str]
    debate_transcript: List[DebateMessage] = Field(default_factory=list)
    agent_traces: List[AgentTraceLog] = Field(default_factory=list)
    evidence_citations: List[GuidelineEvidence] = Field(default_factory=list)

class RiskReport(BaseModel):
    report_id: str
    twin_id: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    patient_summary: Dict[str, Any]
    assessments: Dict[str, CancerRiskAssessment]
    aggregate_baseline_risk_score: float
    aggregate_simulated_risk_score: float
    primary_preventive_opportunities: List[str]
    pre_simulation_recommendations: List[PreSimulationRecommendationItem] = Field(default_factory=list)
    clinical_narrative: str
    feasibility_audit: Optional[Dict[str, Any]] = None
    agent_traces: List[AgentTraceLog] = Field(default_factory=list)
