from typing import Optional, List
from pydantic import BaseModel, Field

class ProceduresPerformed(BaseModel):
    chemotherapy: bool = Field(default=False, description="Received adjuvant or neoadjuvant cytotoxic chemotherapy")
    chemotherapy_details: Optional[str] = Field(default=None, description="Regimen (e.g., FOLFOX, AC-T, Cisplatin/Etoposide)")
    radiation_therapy: bool = Field(default=False, description="Received external beam radiotherapy or brachytherapy")
    radiation_site: Optional[str] = Field(default=None, description="Irradiated anatomical site (e.g., Left Breast, Pelvis, Thorax)")
    surgery_performed: bool = Field(default=False, description="Underwent surgical resection of primary tumor")
    surgical_margin: str = Field(default="R0", description="'R0' (microscopically negative), 'R1' (microscopically positive), 'R2' (gross residual)")
    t_cell_immunotherapy: bool = Field(default=False, description="Received checkpoint inhibitors (anti-PD-1/PD-L1) or CAR-T cell therapy")
    immunotherapy_details: Optional[str] = Field(default=None, description="Agent used (e.g., Pembrolizumab, Tisagenlecleucel)")

class TumorBiomarkers(BaseModel):
    psa_ng_ml: Optional[float] = Field(default=None, description="Prostate-Specific Antigen (normal < 4.0 ng/mL)")
    cea_ng_ml: Optional[float] = Field(default=None, description="Carcinoembryonic Antigen (normal < 3.0 ng/mL for non-smokers)")
    ca125_u_ml: Optional[float] = Field(default=None, description="Cancer Antigen 125 (normal < 35 U/mL)")
    ctdna_status: str = Field(default="unknown", description="'negative' (undetected MRD), 'positive' (persistent MRD), 'unknown'")
    genomic_alterations: Optional[str] = Field(default=None, description="Actionable somatic mutations (e.g., 'BRAF V600E', 'KRAS G12C', 'RET fusion', 'NTRK fusion', 'HER2 exon 20')")

class PriorCancerHistory(BaseModel):
    has_prior_cancer: bool = Field(default=False, description="Whether the patient has a prior confirmed cancer diagnosis")
    primary_cancer_type: Optional[str] = Field(default="Colorectal", description="Primary cancer site: 'Colorectal', 'Breast', 'Lung', 'Prostate', 'Cervical', 'Melanoma', 'Other'")
    stage_at_diagnosis: Optional[str] = Field(default="Stage II", description="'Stage I', 'Stage II', 'Stage III', 'Stage IV'")
    years_since_diagnosis: float = Field(default=2.5, ge=0.0, description="Elapsed years since initial tissue diagnosis")
    years_in_remission: float = Field(default=2.0, ge=0.0, description="Elapsed disease-free years since completion of primary definitive therapy")
    procedures: ProceduresPerformed = Field(default_factory=ProceduresPerformed)
    biomarkers: TumorBiomarkers = Field(default_factory=TumorBiomarkers)
    current_medications: str = Field(default="", description="Manual entry for current medications (e.g., 'Capecitabine, Aspirin 81mg, Metformin')")
    preventive_surveillance_adherent: bool = Field(default=True, description="Strict adherence to surveillance imaging and follow-up lab protocols")
    additional_clinical_notes: Optional[str] = None
