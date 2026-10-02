import copy
from typing import Dict, Any, Optional
from src.agents.base import BaseAgent
from src.models.patient import DigitalTwinState, PatientProfile
from src.models.simulation import WhatIfScenario, CounterfactualState
from src.models.risk_report import CancerRiskAssessment, RiskTrajectoryPoint
from src.rag.retriever import OncologyRetriever
from src.utils.risk_calculators import (
    calculate_lung_risk,
    calculate_colorectal_risk,
    calculate_breast_risk,
    calculate_cervical_risk,
    calculate_prostate_risk,
    generate_risk_trajectory
)

class WhatIfSimulatorAgent(BaseAgent):
    """Agent responsible for running counterfactual 'What-If' simulations on a patient's digital twin across 5 cancers."""

    def __init__(self, retriever: Optional[OncologyRetriever] = None):
        super().__init__(
            name="What-If Simulation Agent",
            role="Projects counterfactual risk reductions and intervention trajectories using clinical trial evidence"
        )
        self.retriever = retriever or OncologyRetriever()

    def run(
        self,
        twin_state: DigitalTwinState,
        scenario: WhatIfScenario,
        baseline_assessments: Dict[str, CancerRiskAssessment]
    ) -> Dict[str, CancerRiskAssessment]:
        self.clear_traces()
        interventions = scenario.interventions
        self.log(
            step_title="Initializing What-If Simulation",
            details=f"Evaluating scenario '{scenario.scenario_title}' over {scenario.time_horizon_years}-year time horizon across 5 oncologic domains."
        )

        # Clone profile to create counterfactual state
        cf_profile = copy.deepcopy(twin_state.patient_profile)
        applied_dict = {}

        # 1. Apply smoking cessation intervention
        if interventions.smoking_cessation and cf_profile.lifestyle.smoking_status != "never":
            cf_profile.lifestyle.smoking_status = "former"
            cf_profile.lifestyle.years_since_quitting = float(scenario.time_horizon_years)
            applied_dict["smoking_cessation"] = True
            self.log(
                step_title="Applied Intervention: Smoking Cessation",
                details=f"Simulating {scenario.time_horizon_years} years of continuous abstinence from tobacco."
            )

        # 2. Apply BMI reduction
        if interventions.target_bmi and interventions.target_bmi < cf_profile.lifestyle.bmi:
            old_bmi = cf_profile.lifestyle.bmi
            cf_profile.lifestyle.bmi = interventions.target_bmi
            applied_dict["target_bmi"] = interventions.target_bmi
            self.log(
                step_title="Applied Intervention: Metabolic Optimization",
                details=f"Target BMI adjusted from {old_bmi:.1f} to {interventions.target_bmi:.1f}."
            )

        # 3. Apply alcohol reduction
        if interventions.target_alcohol_drinks_week is not None:
            old_alc = cf_profile.lifestyle.alcohol_drinks_per_week
            if interventions.target_alcohol_drinks_week < old_alc:
                cf_profile.lifestyle.alcohol_drinks_per_week = interventions.target_alcohol_drinks_week
                applied_dict["target_alcohol_drinks_week"] = interventions.target_alcohol_drinks_week

        # 4. Apply physical activity increase
        if interventions.target_exercise_hours_week is not None:
            if interventions.target_exercise_hours_week > cf_profile.lifestyle.physical_activity_hours_week:
                cf_profile.lifestyle.physical_activity_hours_week = interventions.target_exercise_hours_week
                applied_dict["target_exercise_hours_week"] = interventions.target_exercise_hours_week

        # 5. Apply dietary levers (Fiber, UPF %, Med diet)
        if interventions.target_fiber_grams_day is not None:
            cf_profile.lifestyle.dietary_fiber_grams_day = max(cf_profile.lifestyle.dietary_fiber_grams_day, interventions.target_fiber_grams_day)
            applied_dict["target_fiber_grams_day"] = interventions.target_fiber_grams_day

        if interventions.target_ultra_processed_food_pct is not None:
            cf_profile.lifestyle.ultra_processed_food_pct = min(cf_profile.lifestyle.ultra_processed_food_pct, interventions.target_ultra_processed_food_pct)
            applied_dict["target_ultra_processed_food_pct"] = interventions.target_ultra_processed_food_pct

        if interventions.target_mediterranean_diet_score is not None:
            cf_profile.lifestyle.mediterranean_diet_score = max(cf_profile.lifestyle.mediterranean_diet_score, interventions.target_mediterranean_diet_score)
            applied_dict["target_mediterranean_diet_score"] = interventions.target_mediterranean_diet_score

        # 6. Environmental PM2.5 HEPA filtration
        if interventions.indoor_hepa_pm25_mitigation:
            cf_profile.environmental.pm25_exposure_ug_m3 *= 0.50
            applied_dict["indoor_hepa_pm25_mitigation"] = True
            self.log(
                step_title="Applied Intervention: Indoor HEPA Filtration",
                details="Indoor HEPA filtration modeled: 50% particulate load reduction."
            )

        # 7. HPV Vaccination & Screening
        if interventions.hpv_catchup_vaccine:
            cf_profile.screening.hpv_vaccinated = True
            cf_profile.screening.hpv_vaccine_age_administered = cf_profile.age
            applied_dict["hpv_catchup_vaccine"] = True

        if interventions.adhere_recommended_screening:
            cf_profile.screening.last_pap_smear_years_ago = 1.0
            cf_profile.screening.last_colonoscopy_years_ago = 1.0

        # 8. PSA Screening adherence
        if interventions.psa_screening_adherence or interventions.adhere_recommended_screening:
            cf_profile.screening.last_psa_test_years_ago = 1.0
            applied_dict["psa_screening_adherence"] = True

        simulated_assessments = {}

        # --- Lung Simulation ---
        cf_lung = calculate_lung_risk(cf_profile)
        lung_base = baseline_assessments["Lung"].baseline_risk_pct
        sim_lung_risk = cf_lung["risk_pct"]
        if interventions.adhere_recommended_screening and cf_profile.lifestyle.pack_years >= 20:
            sim_lung_risk *= 0.78  # ~22% mortality reduction from USPSTF LDCT
            applied_dict["ldct_screening"] = True

        sim_lung_risk = round(min(lung_base, sim_lung_risk), 2)
        arr_lung = round(max(0.0, lung_base - sim_lung_risk), 2)
        rrr_lung = round((arr_lung / max(0.01, lung_base)) * 100.0, 1)
        sim_lung_traj = generate_risk_trajectory(lung_base, sim_lung_risk, years=scenario.time_horizon_years)
        sim_lung_evidence = list(baseline_assessments["Lung"].evidence_citations)

        simulated_assessments["Lung"] = CancerRiskAssessment(
            cancer_type="Lung",
            baseline_risk_pct=lung_base,
            counterfactual_risk_pct=sim_lung_risk,
            absolute_risk_reduction_pct=arr_lung,
            relative_risk_reduction_pct=rrr_lung,
            population_average_pct=baseline_assessments["Lung"].population_average_pct,
            risk_category=baseline_assessments["Lung"].risk_category,
            key_drivers=baseline_assessments["Lung"].key_drivers,
            evidence_citations=sim_lung_evidence,
            trajectory=sim_lung_traj
        )

        # --- Colorectal Simulation ---
        cf_crc = calculate_colorectal_risk(cf_profile)
        crc_base = baseline_assessments["Colorectal"].baseline_risk_pct
        sim_crc_risk = cf_crc["risk_pct"]
        if interventions.adhere_recommended_screening:
            sim_crc_risk *= 0.45  # ~55% reduction from colonoscopy polypectomy (USPSTF)
            applied_dict["colonoscopy_screening"] = True

        sim_crc_risk = round(min(crc_base, sim_crc_risk), 2)
        arr_crc = round(max(0.0, crc_base - sim_crc_risk), 2)
        rrr_crc = round((arr_crc / max(0.01, crc_base)) * 100.0, 1)
        sim_crc_traj = generate_risk_trajectory(crc_base, sim_crc_risk, years=scenario.time_horizon_years)
        sim_crc_evidence = list(baseline_assessments["Colorectal"].evidence_citations)

        simulated_assessments["Colorectal"] = CancerRiskAssessment(
            cancer_type="Colorectal",
            baseline_risk_pct=crc_base,
            counterfactual_risk_pct=sim_crc_risk,
            absolute_risk_reduction_pct=arr_crc,
            relative_risk_reduction_pct=rrr_crc,
            population_average_pct=baseline_assessments["Colorectal"].population_average_pct,
            risk_category=baseline_assessments["Colorectal"].risk_category,
            key_drivers=baseline_assessments["Colorectal"].key_drivers,
            evidence_citations=sim_crc_evidence,
            trajectory=sim_crc_traj
        )

        # --- Breast Simulation ---
        cf_breast = calculate_breast_risk(cf_profile)
        breast_base = baseline_assessments["Breast"].baseline_risk_pct
        sim_breast_risk = cf_breast["risk_pct"]
        if interventions.adhere_recommended_screening and cf_profile.biological_sex.lower() == "female":
            sim_breast_risk *= 0.80  # ~20% mortality/advanced reduction
            applied_dict["mammography_screening"] = True

        sim_breast_risk = round(min(breast_base, sim_breast_risk), 2)
        arr_breast = round(max(0.0, breast_base - sim_breast_risk), 2)
        rrr_breast = round((arr_breast / max(0.01, breast_base)) * 100.0, 1)
        sim_breast_traj = generate_risk_trajectory(breast_base, sim_breast_risk, years=scenario.time_horizon_years)
        sim_breast_evidence = list(baseline_assessments["Breast"].evidence_citations)

        simulated_assessments["Breast"] = CancerRiskAssessment(
            cancer_type="Breast",
            baseline_risk_pct=breast_base,
            counterfactual_risk_pct=sim_breast_risk,
            absolute_risk_reduction_pct=arr_breast,
            relative_risk_reduction_pct=rrr_breast,
            population_average_pct=baseline_assessments["Breast"].population_average_pct,
            risk_category=baseline_assessments["Breast"].risk_category,
            key_drivers=baseline_assessments["Breast"].key_drivers,
            evidence_citations=sim_breast_evidence,
            trajectory=sim_breast_traj
        )

        # --- Cervical Simulation ---
        cf_cerv = calculate_cervical_risk(cf_profile)
        cerv_base = baseline_assessments["Cervical"].baseline_risk_pct
        sim_cerv_risk = cf_cerv["risk_pct"]
        if interventions.adhere_recommended_screening and cf_profile.biological_sex.lower() == "female":
            sim_cerv_risk *= 0.70  # ~30% further reduction from strict cytology co-testing

        sim_cerv_risk = round(min(cerv_base, sim_cerv_risk), 2)
        arr_cerv = round(max(0.0, cerv_base - sim_cerv_risk), 2)
        rrr_cerv = round((arr_cerv / max(0.01, cerv_base)) * 100.0, 1)
        sim_cerv_traj = generate_risk_trajectory(cerv_base, sim_cerv_risk, years=scenario.time_horizon_years)
        sim_cerv_evidence = list(baseline_assessments["Cervical"].evidence_citations)

        simulated_assessments["Cervical"] = CancerRiskAssessment(
            cancer_type="Cervical",
            baseline_risk_pct=cerv_base,
            counterfactual_risk_pct=sim_cerv_risk,
            absolute_risk_reduction_pct=arr_cerv,
            relative_risk_reduction_pct=rrr_cerv,
            population_average_pct=baseline_assessments["Cervical"].population_average_pct,
            risk_category=baseline_assessments["Cervical"].risk_category,
            key_drivers=baseline_assessments["Cervical"].key_drivers,
            evidence_citations=sim_cerv_evidence,
            trajectory=sim_cerv_traj
        )

        # --- Prostate Simulation ---
        cf_prost = calculate_prostate_risk(cf_profile)
        prost_base = baseline_assessments["Prostate"].baseline_risk_pct
        sim_prost_risk = cf_prost["risk_pct"]
        if (interventions.psa_screening_adherence or interventions.adhere_recommended_screening) and cf_profile.biological_sex.lower() == "male":
            sim_prost_risk *= 0.80  # ~20% mortality/advanced reduction via shared-decision PSA screening

        sim_prost_risk = round(min(prost_base, sim_prost_risk), 2)
        arr_prost = round(max(0.0, prost_base - sim_prost_risk), 2)
        rrr_prost = round((arr_prost / max(0.01, prost_base)) * 100.0, 1)
        sim_prost_traj = generate_risk_trajectory(prost_base, sim_prost_risk, years=scenario.time_horizon_years)
        sim_prost_evidence = list(baseline_assessments["Prostate"].evidence_citations)

        simulated_assessments["Prostate"] = CancerRiskAssessment(
            cancer_type="Prostate",
            baseline_risk_pct=prost_base,
            counterfactual_risk_pct=sim_prost_risk,
            absolute_risk_reduction_pct=arr_prost,
            relative_risk_reduction_pct=rrr_prost,
            population_average_pct=baseline_assessments["Prostate"].population_average_pct,
            risk_category=baseline_assessments["Prostate"].risk_category,
            key_drivers=baseline_assessments["Prostate"].key_drivers,
            evidence_citations=sim_prost_evidence,
            trajectory=sim_prost_traj
        )

        self.log(
            step_title="5-Cancer Simulation Modeling Finished",
            details=(
                f"Counterfactual simulation completed for {scenario.time_horizon_years} years. "
                f"Absolute risk reductions: Lung -{arr_lung}%, CRC -{arr_crc}%, Breast -{arr_breast}%, "
                f"Cervical -{arr_cerv}%, Prostate -{arr_prost}%."
            )
        )

        return simulated_assessments
