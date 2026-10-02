"""Pipeline verification test for CancerTwin AI (5 cancers + Pre-Simulation Guidance)."""

def test_pipeline():
    from src.models.patient import PatientProfile, LifestyleFactors, GeneticHistory, EnvironmentalFactors, ScreeningHistory
    from src.models.simulation import WhatIfScenario, InterventionParameters
    from src.agents.coordinator import TwinCoordinatorAgent

    # 1. Setup mock patient profile with 5-cancer and environmental variables
    profile = PatientProfile(
        patient_id="TEST-PT-001",
        age=55,
        biological_sex="female",
        genetics=GeneticHistory(
            brca_mutation=True,
            ancestry="ashkenazi_jewish",
            family_cancer_history=["Mother: Breast 45yo", "Aunt: Ovarian 52yo"]
        ),
        lifestyle=LifestyleFactors(
            smoking_status="current",
            pack_years=25.0,
            bmi=28.5,
            alcohol_drinks_per_week=6.0,
            physical_activity_hours_week=1.5,
            dietary_fiber_grams_day=14.0,
            ultra_processed_food_pct=38.0,
            mediterranean_diet_score=4
        ),
        environmental=EnvironmentalFactors(
            pm25_exposure_ug_m3=32.0,
            residential_radon_risk="moderate"
        ),
        screening=ScreeningHistory(
            last_pap_smear_years_ago=4.5,
            hpv_vaccinated=False
        )
    )

    # 2. Setup What-If Scenario with extended levers and 20-year horizon
    scenario = WhatIfScenario(
        twin_id="TEST-TWIN-001",
        scenario_title="Comprehensive 5-Cancer Risk Reduction",
        interventions=InterventionParameters(
            smoking_cessation=True,
            target_bmi=24.0,
            target_exercise_hours_week=3.5,
            adhere_recommended_screening=True,
            target_fiber_grams_day=30.0,
            target_ultra_processed_food_pct=12.0,
            indoor_hepa_pm25_mitigation=True,
            hpv_catchup_vaccine=True
        ),
        time_horizon_years=20
    )

    # 3. Run Pipeline
    coordinator = TwinCoordinatorAgent()
    report = coordinator.run_full_pipeline(profile, scenario)

    # Assertions
    assert report.twin_id is not None
    assert "Lung" in report.assessments
    assert "Breast" in report.assessments
    assert "Colorectal" in report.assessments
    assert "Cervical" in report.assessments
    assert "Prostate" in report.assessments
    assert len(report.pre_simulation_recommendations) > 0
    assert report.assessments["Lung"].absolute_risk_reduction_pct > 0.0
    assert len(report.agent_traces) > 0
    assert len(report.clinical_narrative) > 20
    assert len(report.assessments["Lung"].trajectory) == 20

    print("5-Cancer Pipeline Verification Passed!")
    print(f"Twin ID: {report.twin_id}")
    print(f"Pre-Simulation Recommendations: {len(report.pre_simulation_recommendations)} items generated.")
    print(f"Aggregate Baseline Risk: {report.aggregate_baseline_risk_score}%")
    print(f"Aggregate Simulated Risk: {report.aggregate_simulated_risk_score}%")
    for cancer, assess in report.assessments.items():
        print(f"[{cancer}] Baseline: {assess.baseline_risk_pct}% -> Simulated: {assess.counterfactual_risk_pct}% (-{assess.absolute_risk_reduction_pct}% ARR)")

if __name__ == "__main__":
    test_pipeline()
