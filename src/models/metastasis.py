from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class MetastasisTravelPath(BaseModel):
    source_organ: str
    target_organ: str
    organotropism_affinity_score: float = Field(..., description="Anatomical seed-and-soil biological affinity 0.0 - 1.0")
    typical_travel_route: str = Field(..., description="Vascular, lymphatic, or peritoneal dissemination pathway")
    latency_years_peak: float = Field(..., description="Peak recurrence window in years")

class MetastasisAnalysisRequest(BaseModel):
    prior_primary_cancer: str = Field(default="Colorectal", description="'Colorectal', 'Breast', 'Lung', 'Prostate', 'Cervical', 'Melanoma'")
    prior_stage: str = Field(default="Stage III", description="'Stage I', 'Stage II', 'Stage III', 'Stage IV'")
    new_lesion_site: str = Field(default="Liver", description="Anatomical site of newly detected lesion: 'Liver', 'Lungs', 'Bone', 'Brain', 'Peritoneum', 'Adrenals', 'Cervical/Pelvic Lymph Nodes'")
    disease_free_interval_years: float = Field(default=2.5, ge=0.0, description="Elapsed disease-free years between completion of cure/therapy and discovery of new lesion")
    prior_radiation_field: Optional[str] = Field(default=None, description="Prior irradiated anatomical region if any")
    prior_chemotherapy_regimen: Optional[str] = Field(default=None, description="Prior systemic chemotherapy regimen")
    elevated_primary_marker: bool = Field(default=True, description="Whether original tumor marker (e.g., CEA, PSA, CA-125) is elevated with the new lesion")
    ctdna_positive: bool = Field(default=False, description="Circulating tumor DNA detected")

class MetastasisAnalysisResponse(BaseModel):
    prior_primary: str
    new_lesion_site: str
    disease_free_interval_years: float
    metastasis_probability_pct: float = Field(..., ge=0.0, le=100.0, description="Calculated probability that new lesion is a metastatic seeding from the prior primary")
    second_primary_probability_pct: float = Field(..., ge=0.0, le=100.0, description="Calculated probability that new lesion represents a distinct, de novo second primary malignancy")
    organotropism_score: float = Field(..., ge=0.0, le=1.0)
    organotropism_explanation: str
    travel_route_mechanism: str
    dfi_latency_assessment: str
    radiation_secondary_risk: str
    recommended_diagnostic_workup: List[str]
    molecular_confirmation_markers: List[str]
