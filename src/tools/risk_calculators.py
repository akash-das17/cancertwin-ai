"""
Clinical Risk Calculation Tools.
Pure deterministic mathematical tools for cancer risk projection (Gail, Bach, USPSTF, SEER baseline).
Standard of care / SaMD compliant with 0 LLM hallucinations in the arithmetic.
"""
from typing import Dict, Any, List
from src.models.patient import PatientProfile
from src.utils.risk_calculators import (
    calculate_lung_risk,
    calculate_colorectal_risk,
    calculate_breast_risk,
    calculate_cervical_risk,
    calculate_prostate_risk,
    generate_risk_trajectory
)

def evaluate_all_cancer_risks(profile: PatientProfile) -> Dict[str, Dict[str, Any]]:
    """Tool that runs all 5 validated empirical risk calculators."""
    return {
        "Lung": calculate_lung_risk(profile),
        "Colorectal": calculate_colorectal_risk(profile),
        "Breast": calculate_breast_risk(profile),
        "Cervical": calculate_cervical_risk(profile),
        "Prostate": calculate_prostate_risk(profile),
    }

__all__ = [
    "calculate_lung_risk",
    "calculate_colorectal_risk",
    "calculate_breast_risk",
    "calculate_cervical_risk",
    "calculate_prostate_risk",
    "generate_risk_trajectory",
    "evaluate_all_cancer_risks"
]
