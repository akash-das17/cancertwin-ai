"""
Pharmacology Engine for Tumor Board Therapeutic & Toxicity Simulation.
Models:
1. 5-Year Relapse-Free Survival (RFS) trajectories comparing baseline vs. adjusted regimens.
2. Pharmacokinetic CYP450 metabolic collisions, QTc prolongation, and bleeding toxicity hazard curves.
"""
from typing import List, Dict, Any
from src.models.therapeutic_simulation import (
    TherapeuticSimulationRequest,
    TherapeuticSimulationResponse,
    SurvivalTrajectoryPoint,
    ToxicityHazardPoint,
    DDIAlert
)

def simulate_therapeutic_and_toxicity(req: TherapeuticSimulationRequest) -> TherapeuticSimulationResponse:
    stage_base = {
        "Stage I": 12.0,
        "Stage II": 28.0,
        "Stage III": 52.0,
        "Stage IV": 82.0
    }.get(req.stage, 45.0)

    # 1. Baseline Relapse Calculation
    base_margin_mult = 1.0
    if req.surgical_margin == "R1":
        base_margin_mult = 1.45
    elif req.surgical_margin == "R2":
        base_margin_mult = 1.90

    base_ctdna_mult = 1.55 if req.ctdna_status.lower() == "positive" else 0.70

    baseline_relapse = min(96.0, max(5.0, stage_base * base_margin_mult * base_ctdna_mult))

    # 2. Simulated Relapse with Levers
    sim_margin_mult = base_margin_mult
    if req.re_excision_performed:
        # Re-excision converts R1/R2 to clear margin equivalent
        sim_margin_mult = 1.0
    elif req.sbrt_bed_boost:
        # Radiation bed boost sterilizes residual margin cells
        sim_margin_mult = 1.0 + (base_margin_mult - 1.0) * 0.35

    # Systemic therapy efficacy factor
    therapy = req.selected_systemic_therapy.lower()
    systemic_hr = 1.0
    if "selpercatinib" in therapy or "targeted tki" in therapy or "osimertinib" in therapy:
        systemic_hr = 0.58 if req.ctdna_status.lower() == "positive" else 0.65
    elif "chemotherapy" in therapy or "folfox" in therapy or "capox" in therapy:
        systemic_hr = 0.72
    elif "immunotherapy" in therapy or "pembrolizumab" in therapy:
        systemic_hr = 0.68
    elif "none" in therapy or "observation" in therapy:
        systemic_hr = 1.0

    simulated_relapse = min(95.0, max(4.0, stage_base * sim_margin_mult * base_ctdna_mult * systemic_hr))

    # 5-Year Survival Trajectory (Annual RFS %)
    survival_trajectory: List[SurvivalTrajectoryPoint] = []
    for yr in range(1, 6):
        # Relapse risk distributes across 5 years with highest hazard in yrs 1-2
        hazard_fraction = 1.0 - (0.88 ** yr)
        yr_base_relapse = baseline_relapse * (hazard_fraction / (1.0 - (0.88 ** 5)))
        yr_sim_relapse = simulated_relapse * (hazard_fraction / (1.0 - (0.88 ** 5)))

        base_rfs = round(max(3.0, 100.0 - yr_base_relapse), 1)
        sim_rfs = round(max(3.0, 100.0 - yr_sim_relapse), 1)
        delta = round(sim_rfs - base_rfs, 1)

        survival_trajectory.append(SurvivalTrajectoryPoint(
            year=yr,
            baseline_rfs_pct=base_rfs,
            simulated_rfs_pct=sim_rfs,
            survival_delta_pct=delta
        ))

    # 3. Drug-Drug Interaction (DDI) & Toxicity Hazard Modeling
    active_meds_text = " ".join(req.active_medications).lower()
    ddi_alerts: List[DDIAlert] = []
    has_lethal_ddi = False
    base_toxicity_hazard = 12.0  # standard baseline drug toxicity

    # Collision 1: TKI + Amiodarone (CYP3A4 inhibition + QTc prolongation)
    if ("selpercatinib" in therapy or "tki" in therapy or "osimertinib" in therapy) and "amiodarone" in active_meds_text:
        has_lethal_ddi = True
        ddi_alerts.append(DDIAlert(
            severity="CRITICAL_FATAL",
            title="Lethal CYP3A4 & Cardiac QTc Collision",
            interacting_drugs=[req.selected_systemic_therapy, "Amiodarone"],
            mechanism="Amiodarone is a potent CYP3A4 inhibitor and hERG channel blocker. Co-administration surges TKI serum concentration by 240% while compounding cardiac repolarization delay (QTc > 520 ms).",
            clinical_risk="Life-threatening polymorphic ventricular tachycardia (Torsades de Pointes), cardiogenic collapse, and sudden arrhythmic death.",
            recommended_mitigation="HOLD TKI initiation immediately. Replace Amiodarone with beta-blocker or non-QT-prolonging alternative under cardiology supervision with continuous ECG telemetry."
        ))

    # Collision 2: Warfarin + Targeted TKI or Fluoropyrimidines (Chemo)
    if "warfarin" in active_meds_text and ("chemotherapy" in therapy or "folfox" in therapy or "capecitabine" in therapy or "tki" in therapy):
        ddi_alerts.append(DDIAlert(
            severity="HIGH_TOXICITY",
            title="Severe Hemorrhagic Coagulopathy Hazard",
            interacting_drugs=[req.selected_systemic_therapy, "Warfarin"],
            mechanism="Metabolic displacement of CYP2C9 and protein binding causes uncontrolled INR escalation (>6.5) and impaired clotting cascade.",
            clinical_risk="Severe gastrointestinal hemorrhage, retroperitoneal hematoma, and fatal hemorrhagic cerebral apoplexy.",
            recommended_mitigation="Transition patient from oral Warfarin to therapeutic Low-Molecular-Weight Heparin (Enoxaparin) or direct factor Xa inhibitor with bi-weekly CBC monitoring."
        ))

    # Collision 3: Chemo + Metoprolol
    if "metoprolol" in active_meds_text and ("chemotherapy" in therapy or "folfox" in therapy):
        ddi_alerts.append(DDIAlert(
            severity="MODERATE",
            title="Compounded Symptomatic Bradycardia & Hypotension",
            interacting_drugs=[req.selected_systemic_therapy, "Metoprolol"],
            mechanism="Chemotherapy-induced autonomic neuropathy synergizes with beta-1 adrenergic blockade.",
            clinical_risk="Syncope, severe sinus bradycardia (HR < 45 bpm), and orthostatic collapse.",
            recommended_mitigation="Titrate Metoprolol dose downward by 50% during infusion cycles; monitor blood pressure and pulse."
        ))

    # 4. Generate 180-Day Cumulative Toxicity Curve
    days = [15, 30, 60, 90, 120, 180]
    ddi_toxicity_hazard: List[ToxicityHazardPoint] = []

    for d in days:
        if has_lethal_ddi:
            # Lethal QTc surge accelerates rapidly within 30-60 days
            if d == 15:
                cum_tox = 28.5
                g3_4 = 18.0
            elif d == 30:
                cum_tox = 58.0
                g3_4 = 44.0
            elif d == 60:
                cum_tox = 79.5
                g3_4 = 68.0
            elif d == 90:
                cum_tox = 86.0
                g3_4 = 75.0
            elif d == 120:
                cum_tox = 89.0
                g3_4 = 80.0
            else:
                cum_tox = 91.5
                g3_4 = 82.5
        elif any(a.severity == "HIGH_TOXICITY" for a in ddi_alerts):
            # High bleeding risk curve
            factor = min(1.0, d / 120.0)
            cum_tox = round(15.0 + (factor * 38.0), 1)
            g3_4 = round(8.0 + (factor * 26.0), 1)
        else:
            # Standard tolerable oncologic toxicity curve
            factor = min(1.0, d / 180.0)
            cum_tox = round(6.0 + (factor * 12.0), 1)
            g3_4 = round(2.0 + (factor * 5.0), 1)

        ddi_toxicity_hazard.append(ToxicityHazardPoint(
            day=d,
            cumulative_toxicity_hazard_pct=cum_tox,
            grade3_4_ae_risk_pct=g3_4
        ))

    # Summary and clinical recommendation text
    abs_gain = round(baseline_relapse - simulated_relapse, 1)
    if has_lethal_ddi:
        rec = (
            f"ALERT: Although the proposed regimen yields a {abs_gain}% reduction in 5-year relapse hazard, "
            f"it is currently CONTRAINDICATED due to a lethal drug interaction between {req.selected_systemic_therapy} "
            f"and Amiodarone (79.5% cumulative Grade 3/4 toxicity hazard by Day 60). Cardiac medication substitution is mandatory prior to initiation."
        )
    else:
        rec = (
            f"The proposed therapeutic regimen achieves a favorable oncologic outcome with a {abs_gain}% absolute gain in 5-year Relapse-Free Survival. "
            f"Toxicity profile is clinically manageable provided baseline monitoring protocols are followed."
        )

    return TherapeuticSimulationResponse(
        cancer_type=req.cancer_type,
        stage=req.stage,
        selected_regimen_summary=f"{req.selected_systemic_therapy} | Re-excision: {'Yes' if req.re_excision_performed else 'No'} | SBRT Boost: {'Yes' if req.sbrt_bed_boost else 'No'}",
        relapse_risk_5yr_baseline_pct=round(baseline_relapse, 1),
        relapse_risk_5yr_simulated_pct=round(simulated_relapse, 1),
        absolute_rfs_gain_pct=abs_gain,
        survival_trajectory=survival_trajectory,
        ddi_toxicity_hazard=ddi_toxicity_hazard,
        ddi_alerts=ddi_alerts,
        lethal_ddi_flag=has_lethal_ddi,
        clinical_recommendation=rec
    )
