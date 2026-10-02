"""
LangGraph Multi-Agent Prevention & What-If Simulation StateGraph.
Orchestrates:
1. IntakeAgent
2. RiskAssessmentAgent (utilizing empirical risk tools + ChromaDB RAG)
3. WhatIfSimulatorAgent (counterfactual optimization)
4. ClinicalFeasibilityAndSafetyAgent (behavioral friction, comorbidity guardrails, Phase 1/Phase 2 staging)
5. TwinCoordinatorAgent (executive clinical narrative synthesis)
"""
import uuid
from typing import TypedDict, Dict, Any, List, Optional
from langgraph.graph import StateGraph, START, END

from src.models.patient import PatientProfile, DigitalTwinState
from src.models.simulation import WhatIfScenario, InterventionParameters
from src.models.risk_report import (
    RiskReport,
    CancerRiskAssessment,
    AgentTraceLog,
    PreSimulationRecommendationItem
)
from src.agents.intake_agent import IntakeAgent
from src.agents.risk_agent import RiskAssessmentAgent
from src.agents.simulation_agent import WhatIfSimulatorAgent
from src.agents.clinical_feasibility_agent import (
    ClinicalFeasibilityAndSafetyAgent,
    ClinicalFeasibilityReport
)
from src.rag.retriever import OncologyRetriever
from src.utils.prompts import generate_clinical_narrative, build_pre_simulation_recommendations

class PreventionSimulationState(TypedDict):
    profile: PatientProfile
    twin_state: Optional[DigitalTwinState]
    scenario: Optional[WhatIfScenario]
    baseline_assessments: Optional[Dict[str, CancerRiskAssessment]]
    simulated_assessments: Optional[Dict[str, CancerRiskAssessment]]
    pre_sim_recommendations: Optional[List[PreSimulationRecommendationItem]]
    feasibility_report: Optional[ClinicalFeasibilityReport]
    traces: List[AgentTraceLog]
    final_report: Optional[RiskReport]

# Shared instances
retriever = OncologyRetriever()
intake_agent = IntakeAgent()
risk_agent = RiskAssessmentAgent(retriever=retriever)
simulation_agent = WhatIfSimulatorAgent(retriever=retriever)
feasibility_agent = ClinicalFeasibilityAndSafetyAgent()

def intake_node(state: PreventionSimulationState) -> Dict[str, Any]:
    profile = state["profile"]
    traces = list(state.get("traces", []))
    
    twin_state = intake_agent.run(profile)
    traces.extend(intake_agent.get_traces())
    
    return {"twin_state": twin_state, "traces": traces}

def risk_assessment_node(state: PreventionSimulationState) -> Dict[str, Any]:
    profile = state["profile"]
    twin_state = state.get("twin_state") or intake_agent.run(profile)
    traces = list(state.get("traces", []))

    baseline_assessments = risk_agent.run(twin_state)
    traces.extend(risk_agent.get_traces())

    recs = build_pre_simulation_recommendations(profile, baseline_assessments)
    traces.append(AgentTraceLog(
        agent_name="Clinical Risk Assessment Agent",
        step_title="Pre-Simulation Action Plan Generated",
        details=f"Synthesized {len(recs)} guideline-directed clinical recommendations across 5 cancers."
    ))

    return {
        "baseline_assessments": baseline_assessments,
        "pre_sim_recommendations": recs,
        "traces": traces
    }

def what_if_simulation_node(state: PreventionSimulationState) -> Dict[str, Any]:
    profile = state["profile"]
    twin_state = state.get("twin_state") or intake_agent.run(profile)
    baseline_assessments = state.get("baseline_assessments") or risk_agent.run(twin_state)
    traces = list(state.get("traces", []))
    scenario = state.get("scenario")

    if scenario is None:
        scenario = WhatIfScenario(
            twin_id=twin_state.twin_id,
            scenario_title="Standard Comprehensive Preventive Optimization",
            interventions=InterventionParameters(
                smoking_cessation=True if profile.lifestyle.smoking_status == "current" else False,
                target_bmi=24.5 if profile.lifestyle.bmi > 26.0 else None,
                target_exercise_hours_week=3.5,
                adhere_recommended_screening=True,
                target_fiber_grams_day=30.0,
                target_ultra_processed_food_pct=15.0,
                target_mediterranean_diet_score=8,
                indoor_hepa_pm25_mitigation=True if profile.environmental.pm25_exposure_ug_m3 >= 25.0 else False,
                hpv_catchup_vaccine=True if not profile.screening.hpv_vaccinated and profile.biological_sex.lower() == "female" else False,
                psa_screening_adherence=True if profile.biological_sex.lower() == "male" and profile.age >= 50 else False
            ),
            time_horizon_years=10
        )

    simulated_assessments = simulation_agent.run(
        twin_state=twin_state,
        scenario=scenario,
        baseline_assessments=baseline_assessments
    )
    traces.extend(simulation_agent.get_traces())

    return {
        "scenario": scenario,
        "simulated_assessments": simulated_assessments,
        "traces": traces
    }

def clinical_feasibility_node(state: PreventionSimulationState) -> Dict[str, Any]:
    profile = state["profile"]
    scenario = state.get("scenario")
    interventions = scenario.interventions if (scenario and scenario.interventions) else InterventionParameters()
    traces = list(state.get("traces", []))

    feasibility_report = feasibility_agent.run(
        profile=profile,
        interventions=interventions
    )
    traces.extend(feasibility_agent.get_traces())

    return {"feasibility_report": feasibility_report, "traces": traces}

def coordinator_synthesis_node(state: PreventionSimulationState) -> Dict[str, Any]:
    profile = state["profile"]
    twin_state = state.get("twin_state") or intake_agent.run(profile)
    scenario = state.get("scenario")
    interventions = scenario.interventions if scenario else None
    baseline_assessments = state.get("baseline_assessments") or {}
    simulated_assessments = state.get("simulated_assessments") or {}
    pre_sim_recs = state.get("pre_sim_recommendations") or []
    feasibility_report = state.get("feasibility_report")
    traces = list(state.get("traces", []))

    traces.append(AgentTraceLog(
        agent_name="Twin Coordinator Agent",
        step_title="Synthesizing Digital Twin Report",
        details="Collated 5-cancer assessments, 30-year trajectory curves, behavioral staging plan, and RAG guideline citations."
    ))

    agg_baseline = round(sum(a.baseline_risk_pct for a in baseline_assessments.values()), 2)
    agg_simulated = round(sum(a.counterfactual_risk_pct for a in simulated_assessments.values()), 2)

    opportunities = []
    for c_type, assess in simulated_assessments.items():
        if assess.absolute_risk_reduction_pct > 0.5:
            opportunities.append(
                f"{c_type}: -{assess.absolute_risk_reduction_pct}% risk reduction ({assess.relative_risk_reduction_pct}% relative decrease)"
            )

    patient_summary = {
        "patient_id": profile.patient_id,
        "age": profile.age,
        "sex": profile.biological_sex,
        "smoking_status": profile.lifestyle.smoking_status,
        "pack_years": profile.lifestyle.pack_years,
        "bmi": profile.lifestyle.bmi,
        "ancestry": profile.genetics.ancestry,
        "pm25_ug_m3": profile.environmental.pm25_exposure_ug_m3,
        "health_score": twin_state.overall_health_score
    }

    def _dump_model(m):
        return m.model_dump() if hasattr(m, "model_dump") else m.dict()

    def _dump_model_exclude_none(m):
        return m.model_dump(exclude_none=True) if hasattr(m, "model_dump") else m.dict(exclude_none=True)

    narrative = generate_clinical_narrative(
        patient_summary=patient_summary,
        assessment_results={k: _dump_model(v) for k, v in simulated_assessments.items()},
        interventions_applied=_dump_model_exclude_none(interventions) if interventions else {}
    )

    final_report = RiskReport(
        report_id=f"REP-{uuid.uuid4().hex[:8].upper()}",
        twin_id=twin_state.twin_id,
        patient_summary=patient_summary,
        assessments=simulated_assessments,
        aggregate_baseline_risk_score=agg_baseline,
        aggregate_simulated_risk_score=agg_simulated,
        primary_preventive_opportunities=opportunities,
        pre_simulation_recommendations=pre_sim_recs,
        clinical_narrative=narrative,
        feasibility_audit=feasibility_report.model_dump() if feasibility_report else None,
        agent_traces=traces
    )

    return {"final_report": final_report, "traces": traces}

# Build LangGraph StateGraph
builder = StateGraph(PreventionSimulationState)

builder.add_node("intake", intake_node)
builder.add_node("risk_assessment", risk_assessment_node)
builder.add_node("what_if_simulation", what_if_simulation_node)
builder.add_node("clinical_feasibility", clinical_feasibility_node)
builder.add_node("coordinator_synthesis", coordinator_synthesis_node)

builder.add_edge(START, "intake")
builder.add_edge("intake", "risk_assessment")
builder.add_edge("risk_assessment", "what_if_simulation")
builder.add_edge("what_if_simulation", "clinical_feasibility")
builder.add_edge("clinical_feasibility", "coordinator_synthesis")
builder.add_edge("coordinator_synthesis", END)

prevention_graph = builder.compile()

def run_prevention_pipeline(profile: PatientProfile, scenario: Optional[WhatIfScenario] = None) -> RiskReport:
    """Executes the compiled LangGraph prevention simulation pipeline."""
    initial_state: PreventionSimulationState = {
        "profile": profile,
        "twin_state": None,
        "scenario": scenario,
        "baseline_assessments": None,
        "simulated_assessments": None,
        "pre_sim_recommendations": None,
        "feasibility_report": None,
        "traces": [],
        "final_report": None
    }
    final_state = prevention_graph.invoke(initial_state)
    return final_state["final_report"]
