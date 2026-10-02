from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
from .patient import PatientProfile

class InterventionParameters(BaseModel):
    smoking_cessation: bool = Field(default=False, description="Patient immediately ceases smoking")
    target_bmi: Optional[float] = Field(default=None, description="Target BMI after structured lifestyle management")
    target_alcohol_drinks_week: Optional[float] = Field(default=None, description="Reduced weekly alcohol intake")
    target_exercise_hours_week: Optional[float] = Field(default=None, description="Increased weekly aerobic exercise")
    adhere_recommended_screening: bool = Field(default=True, description="Strict adherence to USPSTF guideline screenings (LDCT, colonoscopy, mammography, Pap/HPV, PSA)")
    target_fiber_grams_day: Optional[float] = Field(default=None, description="Increase dietary fiber to guideline levels (30g+)")
    target_ultra_processed_food_pct: Optional[float] = Field(default=None, description="Reduce ultra-processed foods to <15% of calories")
    target_mediterranean_diet_score: Optional[int] = Field(default=None, description="Increase Mediterranean diet adherence (scale 0-10)")
    indoor_hepa_pm25_mitigation: bool = Field(default=False, description="Adopt indoor HEPA air filtration reducing PM2.5 inhalation by 50%")
    hpv_catchup_vaccine: bool = Field(default=False, description="Obtain 9-valent HPV catch-up vaccination")
    psa_screening_adherence: bool = Field(default=False, description="Initiate baseline & interval PSA shared decision-making screening")

class WhatIfScenario(BaseModel):
    scenario_id: str = Field(default="SCENARIO-001")
    twin_id: str
    scenario_title: str = Field(default="Comprehensive Preventive Intervention")
    interventions: InterventionParameters
    time_horizon_years: int = Field(default=10, ge=1, le=30)

class CounterfactualState(BaseModel):
    scenario_id: str
    baseline_profile: PatientProfile
    counterfactual_profile: PatientProfile
    interventions_applied: Dict[str, Any]
    projected_trajectory_years: int
