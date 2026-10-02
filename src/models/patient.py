from typing import List, Optional, Any
from pydantic import BaseModel, Field
from datetime import datetime

class GeneticHistory(BaseModel):
    brca_mutation: bool = Field(default=False, description="Presence of BRCA1 or BRCA2 pathogenic variant")
    lynch_syndrome: bool = Field(default=False, description="Hereditary nonpolyposis colorectal cancer (Lynch syndrome)")
    egfr_mutation: bool = Field(default=False, description="EGFR or KRAS mutation carrier")
    ancestry: str = Field(
        default="general",
        description="Genetic ancestry group: 'general', 'ashkenazi_jewish', 'african', 'east_asian', 'caucasian', 'hispanic'"
    )
    family_cancer_history: List[str] = Field(
        default_factory=list,
        description="First-degree relatives diagnosed with cancer (e.g. ['Mother: Breast 48yo', 'Father: Colorectal 56yo', 'Brother: Prostate 54yo'])"
    )
    other_genomic_alterations: Optional[str] = Field(
        default=None,
        description="Additional somatic/germline genomic mutations (e.g. 'NTRK1 fusion', 'BRAF V600E', 'RET fusion', 'KRAS G12C', 'HER2 exon 20')"
    )

class LifestyleFactors(BaseModel):
    smoking_status: str = Field(default="never", description="'never', 'former', 'current'")
    pack_years: float = Field(default=0.0, ge=0.0, description="Packs per day multiplied by years smoked")
    years_since_quitting: Optional[float] = Field(default=None, ge=0.0, description="Years since smoking cessation if former smoker")
    bmi: float = Field(default=24.5, ge=12.0, le=60.0, description="Body Mass Index in kg/m2")
    alcohol_drinks_per_week: float = Field(default=2.0, ge=0.0, description="Standard alcoholic drinks consumed per week")
    physical_activity_hours_week: float = Field(default=2.5, ge=0.0, description="Moderate to vigorous aerobic exercise in hours/week")
    dietary_fiber_grams_day: float = Field(default=18.0, ge=0.0, description="Daily dietary fiber intake in grams")
    red_processed_meat_servings_week: float = Field(default=3.0, ge=0.0, description="Weekly servings of red or processed meats")
    ultra_processed_food_pct: float = Field(default=25.0, ge=0.0, le=100.0, description="Estimated percentage of daily calories from ultra-processed foods")
    mediterranean_diet_score: int = Field(default=6, ge=0, le=10, description="Adherence to Mediterranean diet (0=very poor, 10=exemplary)")

class EnvironmentalFactors(BaseModel):
    pm25_exposure_ug_m3: float = Field(default=18.0, ge=0.0, description="Regional ambient PM2.5 particulate pollution (μg/m3)")
    residential_radon_risk: str = Field(default="low", description="'low', 'moderate', 'high'")
    occupational_carcinogen_exposure: bool = Field(default=False, description="Exposure to asbestos, silica, chemical solvents, or diesel exhaust")

class ScreeningHistory(BaseModel):
    last_colonoscopy_years_ago: Optional[float] = Field(default=None, description="Years since last colonoscopy")
    last_mammogram_years_ago: Optional[float] = Field(default=None, description="Years since last mammogram")
    last_ldct_screening_years_ago: Optional[float] = Field(default=None, description="Years since last low-dose chest CT")
    # Cervical Screening & HPV Vaccine
    last_pap_smear_years_ago: Optional[float] = Field(default=None, description="Years since last Pap smear or HPV co-test")
    hpv_vaccinated: bool = Field(default=False, description="Received 2- or 3-dose HPV vaccination (Gardasil/Cervarix)")
    hpv_vaccine_age_administered: Optional[int] = Field(default=None, description="Age when HPV vaccination completed")
    abnormal_pap_history: bool = Field(default=False, description="History of ASCUS, LSIL, or HSIL on prior cytology")
    # Prostate Screening
    last_psa_test_years_ago: Optional[float] = Field(default=None, description="Years since last serum PSA test")
    baseline_psa_ng_ml: Optional[float] = Field(default=None, description="Most recent baseline serum PSA level (ng/mL)")

class PatientProfile(BaseModel):
    patient_id: str = Field(default="PT-DEMO-001")
    age: int = Field(default=52, ge=18, le=100)
    biological_sex: str = Field(default="female", description="'female', 'male', 'other'")
    genetics: GeneticHistory = Field(default_factory=GeneticHistory)
    lifestyle: LifestyleFactors = Field(default_factory=LifestyleFactors)
    environmental: EnvironmentalFactors = Field(default_factory=EnvironmentalFactors)
    screening: ScreeningHistory = Field(default_factory=ScreeningHistory)
    oncology_history: Optional[Any] = Field(default=None, description="Optional prior cancer and oncologic history")
    notes: Optional[str] = None

class DigitalTwinState(BaseModel):
    twin_id: str
    patient_profile: PatientProfile
    created_at: datetime = Field(default_factory=datetime.utcnow)
    overall_health_score: float = Field(default=75.0, ge=0.0, le=100.0)
    primary_cancer_vulnerabilities: List[str] = Field(default_factory=list)
    state_vector: dict = Field(
        default_factory=dict,
        description="Normalized feature embedding representing physiological risk state"
    )
