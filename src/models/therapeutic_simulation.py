"""
Therapeutic & Toxicity Simulation Models.
Dedicated models for the Virtual Tumor Board's therapeutic regimen evaluation and DDI toxicity curve.
"""
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class TherapeuticSimulationRequest(BaseModel):
    cancer_type: str = "Colorectal"
    stage: str = "Stage III"
    surgical_margin: str = "R1"  # "R0", "R1", "R2"
    ctdna_status: str = "positive"  # "positive", "negative", "unknown"
    re_excision_performed: bool = False
    sbrt_bed_boost: bool = False
    selected_systemic_therapy: str = "Targeted TKI (Selpercatinib / RET inhibitor)"
    active_medications: List[str] = Field(default_factory=lambda: ["Amiodarone (200mg daily)", "Warfarin (5mg daily)"])

class SurvivalTrajectoryPoint(BaseModel):
    year: int
    baseline_rfs_pct: float
    simulated_rfs_pct: float
    survival_delta_pct: float

class ToxicityHazardPoint(BaseModel):
    day: int
    cumulative_toxicity_hazard_pct: float
    grade3_4_ae_risk_pct: float

class DDIAlert(BaseModel):
    severity: str  # "CRITICAL_FATAL", "HIGH_TOXICITY", "MODERATE"
    title: str
    interacting_drugs: List[str]
    mechanism: str
    clinical_risk: str
    recommended_mitigation: str

class TherapeuticSimulationResponse(BaseModel):
    cancer_type: str
    stage: str
    selected_regimen_summary: str
    relapse_risk_5yr_baseline_pct: float
    relapse_risk_5yr_simulated_pct: float
    absolute_rfs_gain_pct: float
    survival_trajectory: List[SurvivalTrajectoryPoint]
    ddi_toxicity_hazard: List[ToxicityHazardPoint]
    ddi_alerts: List[DDIAlert]
    lethal_ddi_flag: bool
    clinical_recommendation: str
