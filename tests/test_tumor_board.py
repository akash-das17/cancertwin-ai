"""Verification tests for 3-Agent Virtual Tumor Board & Metastasis Tracker."""

def test_tumor_board_and_metastasis():
    from src.models.oncology_history import PriorCancerHistory, ProceduresPerformed, TumorBiomarkers
    from src.models.metastasis import MetastasisAnalysisRequest
    from src.agents.tumor_board.supervisor import TumorBoardSupervisorAgent
    from src.utils.metastasis_tracker import analyze_metastasis_vs_second_primary

    # 1. Test Prior Cancer History & 3-Agent Tumor Board Debate
    history = PriorCancerHistory(
        has_prior_cancer=True,
        primary_cancer_type="Colorectal",
        stage_at_diagnosis="Stage III",
        years_since_diagnosis=3.0,
        years_in_remission=2.0,
        procedures=ProceduresPerformed(
            chemotherapy=True,
            chemotherapy_details="FOLFOX 12 cycles",
            surgery_performed=True,
            surgical_margin="R1",  # Microscopic residual margin -> triggers debate
            radiation_therapy=False
        ),
        biomarkers=TumorBiomarkers(
            cea_ng_ml=6.8,  # Elevated CEA
            ctdna_status="positive"  # Persistent MRD -> triggers medical oncology escalation
        ),
        current_medications="Capecitabine 1000mg BID, Low-dose Aspirin",
        preventive_surveillance_adherent=True
    )

    supervisor = TumorBoardSupervisorAgent()
    debate_result = supervisor.adjudicate_debate(history)

    assert debate_result.primary_cancer == "Colorectal"
    assert len(debate_result.agent_opinions) == 3
    assert debate_result.consensus_relapse_risk_5yr_pct > 0.0
    assert len(debate_result.key_debate_points) > 0
    assert len(debate_result.action_plan) > 0
    assert len(debate_result.adjudication_rationale) > 20

    print("Tumor Board Verification Passed!")
    print(f"Consensus 5-Year Relapse Risk: {debate_result.consensus_relapse_risk_5yr_pct}% ({debate_result.risk_tier})")
    print(f"Medical Oncologist Assessment: {debate_result.agent_opinions[0].assessed_relapse_risk_pct}%")
    print(f"Surgical Oncologist Assessment: {debate_result.agent_opinions[1].assessed_relapse_risk_pct}%")
    print(f"Radiation Oncologist Assessment: {debate_result.agent_opinions[2].assessed_relapse_risk_pct}%")
    for pt in debate_result.key_debate_points:
        print(f" - {pt}")

    # 2. Test Metastasis vs Second Primary Tracker
    # Scenario: Colon cancer with new liver lesion 1.5 years later
    met_req = MetastasisAnalysisRequest(
        prior_primary_cancer="Colorectal",
        prior_stage="Stage III",
        new_lesion_site="Liver",
        disease_free_interval_years=1.5,
        elevated_primary_marker=True,
        ctdna_positive=True
    )
    met_res = analyze_metastasis_vs_second_primary(met_req)

    assert met_res.metastasis_probability_pct > 70.0  # High organotropism and short latency
    assert met_res.second_primary_probability_pct < 30.0
    assert "portal venous" in met_res.travel_route_mechanism.lower() or "sinusoidal" in met_res.travel_route_mechanism.lower()
    assert len(met_res.recommended_diagnostic_workup) > 0

    print("\nMetastasis Tracker Verification Passed!")
    print(f"New Lesion Site: {met_res.new_lesion_site} after {met_res.disease_free_interval_years} yrs")
    print(f"Metastatic Recurrence Likelihood: {met_res.metastasis_probability_pct}%")
    print(f"Second Primary Likelihood: {met_res.second_primary_probability_pct}%")
    print(f"Travel Route Mechanism: {met_res.travel_route_mechanism}")

if __name__ == "__main__":
    test_tumor_board_and_metastasis()
