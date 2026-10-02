"""
Clinical Contraindication and Behavioral Feasibility Tool.
Deterministic safety guardrail checking for proposed lifestyle, screening, and chemoprevention changes.
"""
from typing import Dict, Any, List
from src.models.patient import PatientProfile
from src.models.simulation import InterventionParameters

def audit_contraindications_and_feasibility(
    profile: PatientProfile,
    interventions: InterventionParameters
) -> Dict[str, Any]:
    """
    Evaluates proposed counterfactual interventions against clinical contraindications
    and patient lifestyle friction / behavioral feasibility.
    """
    contraindications: List[str] = []
    safety_warnings: List[str] = []
    feasibility_friction_score: int = 0  # 0 to 10 scale of adherence collapse risk
    friction_factors: List[str] = []

    # Comorbidity & medication extraction
    meds_str = ""
    history_str = ""
    onco_hist = getattr(profile, "oncology_history", None)
    if onco_hist:
        meds_str = (getattr(onco_hist, "current_medications", "") or "").lower()
    
    # 1. Aspirin / NSAID chemoprevention audit
    has_bleeding_risk = any(k in meds_str for k in ["warfarin", "eliquis", "apixaban", "xarelto", "rivaroxaban", "plavix", "clopidogrel"])
    if getattr(interventions, "aspirin_chemoprevention", False):
        if has_bleeding_risk:
            contraindications.append(
                "CRITICAL CONTRAINDICATION: Daily aspirin chemoprevention is unsafe due to concurrent anticoagulant / antiplatelet therapy (severe gastrointestinal/cerebral hemorrhage hazard)."
            )
        elif "ulcer" in history_str or "gastritis" in history_str:
            safety_warnings.append(
                "SAFETY WARNING: History of peptic ulcer / gastritis requires co-prescription of a proton-pump inhibitor (PPI) if aspirin is initiated."
            )

    # 2. Exercise escalation feasibility & safety
    target_ex = interventions.target_exercise_hours_week or profile.lifestyle.physical_activity_hours_week
    ex_delta = target_ex - profile.lifestyle.physical_activity_hours_week
    if ex_delta >= 4.0:
        feasibility_friction_score += 3
        friction_factors.append(
            f"Vigorous physical activity increase from {profile.lifestyle.physical_activity_hours_week:.1f} to {target_ex:.1f} hrs/week (+{ex_delta:.1f} hrs) risks musculoskeletal injury and compliance burnout."
        )
    elif ex_delta >= 2.0:
        feasibility_friction_score += 1
        friction_factors.append(f"Moderate physical activity escalation (+{ex_delta:.1f} hrs/week).")

    # 3. Smoking Cessation & Simultaneous Radical Caloric Restriction
    is_quitting_smoke = interventions.smoking_cessation and profile.lifestyle.smoking_status == "current"
    bmi_delta = 0.0
    if interventions.target_bmi and interventions.target_bmi < profile.lifestyle.bmi:
        bmi_delta = profile.lifestyle.bmi - interventions.target_bmi

    if is_quitting_smoke and bmi_delta >= 6.0:
        feasibility_friction_score += 4
        friction_factors.append(
            f"Simultaneous nicotine withdrawal and severe caloric restriction (targeting -{bmi_delta:.1f} BMI units) has high behavioral relapse rates (>80%). Nicotine cravings often trigger compensatory eating."
        )
    elif bmi_delta >= 6.0:
        feasibility_friction_score += 2
        friction_factors.append(f"Aggressive BMI reduction target of -{bmi_delta:.1f} units requires supervised clinical metabolic protocol.")

    # 4. Ultra-Processed Food & Dietary Fiber shift
    if interventions.target_fiber_grams_day and interventions.target_fiber_grams_day > profile.lifestyle.dietary_fiber_grams_day + 15:
        feasibility_friction_score += 1
        friction_factors.append(
            "Rapid high-fiber escalation without gradual titrating induces gastrointestinal distress and adherence abandonment."
        )

    # Compute overall feasibility tier
    if feasibility_friction_score >= 5:
        feasibility_tier = "High Friction (Unrealistic Single-Stage Implementation)"
        staging_recommended = True
    elif feasibility_friction_score >= 3:
        feasibility_tier = "Moderate Friction (Staged Implementation Advised)"
        staging_recommended = True
    else:
        feasibility_tier = "Low Friction (Feasible Near-Term Plan)"
        staging_recommended = False

    # Two-Phase Staging Strategy
    phase_1_actions: List[str] = []
    phase_2_actions: List[str] = []

    if is_quitting_smoke:
        phase_1_actions.append("Phase 1 Priority: Structured nicotine replacement therapy (NRT) + behavioral coaching. Stabilize tobacco cessation first.")
    
    if profile.lifestyle.physical_activity_hours_week < 2.0 and target_ex >= 2.5:
        phase_1_actions.append(f"Phase 1: Initiate walking/aerobic routine building to 2.0 hours/week (gentle ramp-up).")
        phase_2_actions.append(f"Phase 2 (Months 6–12): Advance physical activity to full {target_ex:.1f} hours/week including resistance training.")
    elif target_ex > profile.lifestyle.physical_activity_hours_week:
        phase_1_actions.append(f"Phase 1: Progress physical activity to {target_ex:.1f} hours/week.")

    if interventions.adhere_recommended_screening:
        phase_1_actions.append("Phase 1 Immediate: Complete all overdue guideline-recommended cancer screenings (Colonoscopy, Low-dose CT, Mammography).")

    if bmi_delta > 0:
        initial_loss = min(3.0, bmi_delta)
        phase_1_actions.append(f"Phase 1: Target initial metabolic reduction of -{initial_loss:.1f} BMI units through dietary fiber and reduced UPF.")
        if bmi_delta > initial_loss:
            remaining_loss = bmi_delta - initial_loss
            phase_2_actions.append(f"Phase 2 (Months 6–12): Target consolidation of remaining -{remaining_loss:.1f} BMI units toward target {interventions.target_bmi:.1f}.")

    if interventions.target_fiber_grams_day:
        phase_1_actions.append(f"Phase 1: Titrate dietary fiber by +5g/week up to {interventions.target_fiber_grams_day:.0f}g/day.")

    if interventions.indoor_hepa_pm25_mitigation:
        phase_1_actions.append("Phase 1 Environmental: Install HEPA air purifier in bedroom/living spaces for immediate particulate mitigation.")

    return {
        "contraindications": contraindications,
        "safety_warnings": safety_warnings,
        "feasibility_friction_score": min(10, feasibility_friction_score),
        "feasibility_tier": feasibility_tier,
        "staging_recommended": staging_recommended,
        "friction_factors": friction_factors,
        "phase_1_actions": phase_1_actions,
        "phase_2_actions": phase_2_actions
    }
