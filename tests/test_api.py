"""Direct endpoint verification test for CancerTwin AI (5 Cancers, Recommendations, Relapse, Metastasis)."""
import asyncio
from src.api.app import (
    health_check,
    create_twin_profile,
    run_simulation,
    get_pre_simulation_recommendations,
    evaluate_prior_cancer_relapse,
    evaluate_metastasis_vs_second_primary,
    SimulationRequest
)
from src.models.patient import PatientProfile, LifestyleFactors, GeneticHistory, EnvironmentalFactors, ScreeningHistory
from src.models.simulation import InterventionParameters
from src.models.oncology_history import PriorCancerHistory, ProceduresPerformed, TumorBiomarkers
from src.models.metastasis import MetastasisAnalysisRequest

def test_endpoints():
    # 1. Test Health
    health = asyncio.run(health_check())
    assert health["status"] == "healthy"
    assert "Cervical" in health["cancers_supported"]
    assert "Prostate" in health["cancers_supported"]
    print("[API Test] Health check OK:", health)

    # 2. Test Twin Profile
    profile = PatientProfile(
        patient_id="API-PT-001",
        age=52,
        biological_sex="female",
        genetics=GeneticHistory(brca_mutation=True, ancestry="ashkenazi_jewish"),
        lifestyle=LifestyleFactors(
            smoking_status="former",
            pack_years=15.0,
            years_since_quitting=4.0,
            bmi=26.0,
            dietary_fiber_grams_day=16.0,
            ultra_processed_food_pct=30.0
        ),
        environmental=EnvironmentalFactors(pm25_exposure_ug_m3=28.0),
        screening=ScreeningHistory(hpv_vaccinated=False, last_pap_smear_years_ago=4.0)
    )
    twin_state = asyncio.run(create_twin_profile(profile))
    assert twin_state.twin_id.startswith("TWIN-")
    print(f"[API Test] Twin Profile OK: {twin_state.twin_id} (Health Score: {twin_state.overall_health_score})")

    # 3. Test Pre-Simulation Recommendations
    rec_res = asyncio.run(get_pre_simulation_recommendations(profile))
    assert len(rec_res["recommendations"]) > 0
    print(f"[API Test] Pre-Simulation Recommendations OK: {len(rec_res['recommendations'])} items generated.")

    # 4. Test 5-Cancer Simulation
    req = SimulationRequest(
        profile=profile,
        interventions=InterventionParameters(
            smoking_cessation=True,
            target_bmi=23.0,
            target_exercise_hours_week=3.0,
            adhere_recommended_screening=True,
            indoor_hepa_pm25_mitigation=True,
            hpv_catchup_vaccine=True
        ),
        time_horizon_years=15,
        scenario_title="API Direct Test Scenario"
    )
    report = asyncio.run(run_simulation(req))
    assert report.twin_id == twin_state.twin_id or report.twin_id.startswith("TWIN-")
    assert "Lung" in report.assessments
    assert "Breast" in report.assessments
    assert "Colorectal" in report.assessments
    assert "Cervical" in report.assessments
    assert "Prostate" in report.assessments
    assert len(report.pre_simulation_recommendations) > 0
    print("[API Test] 5-Cancer Simulation Endpoint OK. Generated report:", report.report_id)

    # 5. Test Prior Cancer & Virtual Tumor Board Relapse
    prior_hist = PriorCancerHistory(
        has_prior_cancer=True,
        primary_cancer_type="Breast",
        stage_at_diagnosis="Stage II",
        years_in_remission=3.0,
        procedures=ProceduresPerformed(
            surgery_performed=True,
            surgical_margin="R0",
            chemotherapy=True,
            radiation_therapy=True
        ),
        biomarkers=TumorBiomarkers(ctdna_status="negative"),
        current_medications="Tamoxifen 20mg daily",
        preventive_surveillance_adherent=True
    )
    relapse_res = asyncio.run(evaluate_prior_cancer_relapse(prior_hist))
    assert len(relapse_res.agent_opinions) == 3
    assert relapse_res.consensus_relapse_risk_5yr_pct > 0.0
    print(f"[API Test] Tumor Board Debate OK: Consensus 5-Yr Relapse = {relapse_res.consensus_relapse_risk_5yr_pct}% ({relapse_res.risk_tier})")

    # 6. Test Metastasis vs Second Primary Tracker
    met_req = MetastasisAnalysisRequest(
        prior_primary_cancer="Breast",
        prior_stage="Stage II",
        new_lesion_site="Bone",
        disease_free_interval_years=3.5,
        elevated_primary_marker=True
    )
    met_res = asyncio.run(evaluate_metastasis_vs_second_primary(met_req))
    assert met_res.metastasis_probability_pct > 60.0
    print(f"[API Test] Metastasis Tracker OK: {met_res.prior_primary} -> {met_res.new_lesion_site}: {met_res.metastasis_probability_pct}% Metastasis vs {met_res.second_primary_probability_pct}% Second Primary")

if __name__ == "__main__":
    test_endpoints()
