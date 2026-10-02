"""
LangGraph Multi-Agent Virtual Tumor Board StateGraph.
Orchestrates an interactive cyclical multidisciplinary debate across:
- Medical Oncology Agent
- Surgical Oncology Agent
- Radiation Oncology Agent
- Tumor Board Supervisor Agent
Round 1 (Opening Statements) -> Round 2 (Cyclical Cross-Examination Rebuttals) -> Round 3 (Consensus Adjudication).
No fictional human names or academic degrees.
"""
from typing import TypedDict, List, Optional, Dict, Any
from langgraph.graph import StateGraph, START, END

from src.models.oncology_history import PriorCancerHistory
from src.models.risk_report import (
    TumorBoardAgentOpinion,
    TumorBoardDebateResult,
    AgentTraceLog,
    DebateMessage,
    GuidelineEvidence
)
from src.agents.tumor_board.medical_oncologist import MedicalOncologistAgent
from src.agents.tumor_board.surgical_oncologist import SurgicalOncologistAgent
from src.agents.tumor_board.radiation_oncologist import RadiationOncologistAgent
from src.agents.trial_appraisal_agent import ClinicalTrialAppraisalAgent
from src.rag.retriever import OncologyRetriever
from src.utils.llm_client import get_llm_client

class TumorBoardDebateState(TypedDict):
    history: PriorCancerHistory
    opinions: List[TumorBoardAgentOpinion]
    traces: List[AgentTraceLog]
    transcript: List[DebateMessage]
    round_number: int
    evidence: List[GuidelineEvidence]
    final_result: Optional[TumorBoardDebateResult]

# Agent instances
medical_agent = MedicalOncologistAgent()
surgical_agent = SurgicalOncologistAgent()
radiation_agent = RadiationOncologistAgent()
retriever = OncologyRetriever()
appraisal_agent = ClinicalTrialAppraisalAgent(retriever=retriever)
llm_client = get_llm_client()

def medical_oncology_node(state: TumorBoardDebateState) -> Dict[str, Any]:
    history = state["history"]
    opinions = list(state.get("opinions", []))
    traces = list(state.get("traces", []))
    transcript = list(state.get("transcript", []))
    rnd = state.get("round_number", 1)

    if rnd == 1:
        op, tr = medical_agent.evaluate(history)
        opinions.append(op)
        traces.append(tr)
        transcript.append(DebateMessage(
            round_number=1,
            round_title="Round 1: Opening Specialist Assessment",
            speaker_role=op.agent_role,
            speaker_name=op.specialist_name,
            content=op.reasoning
        ))
    elif rnd == 2:
        # Cross-examine surgical and radiation opinions
        surg_op = next((o for o in opinions if "Surgical" in o.agent_role), opinions[0])
        rad_op = next((o for o in opinions if "Radiation" in o.agent_role), opinions[-1])
        rebuttal = medical_agent.cross_examine_and_rebut(history, surg_op, rad_op)
        transcript.append(DebateMessage(
            round_number=2,
            round_title="Round 2: Cross-Examination & Direct Rebuttal",
            speaker_role=medical_agent.role_name,
            speaker_name=medical_agent.specialist_name,
            target_peer="Surgical & Radiation Oncology",
            content=rebuttal
        ))

    return {"opinions": opinions, "traces": traces, "transcript": transcript}

def surgical_oncology_node(state: TumorBoardDebateState) -> Dict[str, Any]:
    history = state["history"]
    opinions = list(state.get("opinions", []))
    traces = list(state.get("traces", []))
    transcript = list(state.get("transcript", []))
    rnd = state.get("round_number", 1)

    if rnd == 1:
        op, tr = surgical_agent.evaluate(history)
        opinions.append(op)
        traces.append(tr)
        transcript.append(DebateMessage(
            round_number=1,
            round_title="Round 1: Opening Specialist Assessment",
            speaker_role=op.agent_role,
            speaker_name=op.specialist_name,
            content=op.reasoning
        ))
    elif rnd == 2:
        # Cross-examine medical and radiation opinions
        med_op = next((o for o in opinions if "Medical" in o.agent_role), opinions[0])
        rad_op = next((o for o in opinions if "Radiation" in o.agent_role), opinions[-1])
        rebuttal = surgical_agent.cross_examine_and_rebut(history, med_op, rad_op)
        transcript.append(DebateMessage(
            round_number=2,
            round_title="Round 2: Cross-Examination & Direct Rebuttal",
            speaker_role=surgical_agent.role_name,
            speaker_name=surgical_agent.specialist_name,
            target_peer="Medical & Radiation Oncology",
            content=rebuttal
        ))

    return {"opinions": opinions, "traces": traces, "transcript": transcript}

def radiation_oncology_node(state: TumorBoardDebateState) -> Dict[str, Any]:
    history = state["history"]
    opinions = list(state.get("opinions", []))
    traces = list(state.get("traces", []))
    transcript = list(state.get("transcript", []))
    rnd = state.get("round_number", 1)

    if rnd == 1:
        op, tr = radiation_agent.evaluate(history)
        opinions.append(op)
        traces.append(tr)
        transcript.append(DebateMessage(
            round_number=1,
            round_title="Round 1: Opening Specialist Assessment",
            speaker_role=op.agent_role,
            speaker_name=op.specialist_name,
            content=op.reasoning
        ))
        next_rnd = 2
    elif rnd == 2:
        # Cross-examine medical and surgical opinions
        med_op = next((o for o in opinions if "Medical" in o.agent_role), opinions[0])
        surg_op = next((o for o in opinions if "Surgical" in o.agent_role), opinions[1])
        rebuttal = radiation_agent.cross_examine_and_rebut(history, med_op, surg_op)
        transcript.append(DebateMessage(
            round_number=2,
            round_title="Round 2: Cross-Examination & Direct Rebuttal",
            speaker_role=radiation_agent.role_name,
            speaker_name=radiation_agent.specialist_name,
            target_peer="Medical & Surgical Oncology",
            content=rebuttal
        ))
        traces.append(AgentTraceLog(
            agent_name="Tumor Board Supervisor Agent",
            step_title="Cross-Disciplinary Peer Rebuttals",
            details="Completed multi-agent cross-examination round between Medical Oncology, Surgical Oncology, and Radiation Oncology."
        ))
        next_rnd = 3
    else:
        next_rnd = 3

    return {"opinions": opinions, "traces": traces, "transcript": transcript, "round_number": next_rnd}

def debate_router(state: TumorBoardDebateState) -> str:
    """Cyclical debate router: loops back for Round 2, proceeds to evidence for Round 3."""
    if state.get("round_number", 1) == 2:
        return "advance_to_cross_rebuttal"
    return "proceed_to_evidence"

def evidence_retrieval_node(state: TumorBoardDebateState) -> Dict[str, Any]:
    history = state["history"]
    traces = list(state.get("traces", []))

    genomic_note = f", somatic alteration: {history.biomarkers.genomic_alterations}" if history.biomarkers.genomic_alterations else ""
    evidence_query = (
        f"{history.primary_cancer_type} cancer {history.stage_at_diagnosis} relapse recurrence risk, "
        f"ctDNA minimal residual disease, surgical margins, adjuvant systemic radiation therapy{genomic_note}"
    )
    evidence = retriever.retrieve_guidelines(
        query=evidence_query,
        cancer_type=history.primary_cancer_type,
        top_k=3
    )

    if history.biomarkers.genomic_alterations:
        genomic_evidence = retriever.retrieve_guidelines(
            query=f"{history.primary_cancer_type} {history.biomarkers.genomic_alterations} targeted therapy clinical trial",
            cancer_type=history.primary_cancer_type,
            top_k=2
        )
        existing_ids = {e.id for e in evidence}
        for ge in genomic_evidence:
            if ge.id not in existing_ids:
                evidence.append(ge)

    traces.append(AgentTraceLog(
        agent_name="Tumor Board Supervisor Agent",
        step_title="Knowledge Base Query for Relapse & Adjuvant Evidence",
        details=f"Retrieved {len(evidence)} clinical trials and guidelines from ChromaDB / PubMed."
    ))

    # Autonomous Trial Appraisal for all retrieved PubMed trials
    pubmed_trials = [e for e in evidence if e.id.startswith("PUBMED-")]
    for trial in pubmed_trials:
        if not getattr(trial, "appraisal", None):
            try:
                appraisal = appraisal_agent.appraise_trial(
                    paper={"pmid": trial.id.replace("PUBMED-", ""), "title": trial.title, "summary": trial.excerpt},
                    cancer_type=history.primary_cancer_type or "General",
                    biomarker=history.biomarkers.genomic_alterations,
                    stage=history.stage_at_diagnosis
                )
                trial.appraisal = appraisal.model_dump()
                if appraisal.hazard_ratio and not trial.hazard_ratio:
                    trial.hazard_ratio = appraisal.hazard_ratio
            except Exception as e:
                print(f"[EvidenceNode] Appraisal error for {trial.id}: {e}")
    if pubmed_trials:
        traces.extend(appraisal_agent.get_traces())

    return {"evidence": evidence, "traces": traces}

def supervisor_adjudication_node(state: TumorBoardDebateState) -> Dict[str, Any]:
    history = state["history"]
    opinions = state["opinions"]
    traces = list(state.get("traces", []))
    transcript = list(state.get("transcript", []))
    evidence = state.get("evidence", [])

    op_med = opinions[0]
    op_surg = opinions[1]
    op_rad = opinions[2]

    # Weighted consensus math
    consensus_relapse_risk = round(
        (op_med.assessed_relapse_risk_pct * 0.38) +
        (op_surg.assessed_relapse_risk_pct * 0.34) +
        (op_rad.assessed_relapse_risk_pct * 0.28),
        1
    )

    if consensus_relapse_risk < 15.0:
        risk_tier = "Low Relapse Risk"
    elif consensus_relapse_risk < 35.0:
        risk_tier = "Intermediate Relapse Risk"
    elif consensus_relapse_risk < 60.0:
        risk_tier = "High Relapse Risk"
    else:
        risk_tier = "Very High Relapse Risk"

    # Debate friction points
    debate_points = []
    risks = [op.assessed_relapse_risk_pct for op in opinions]
    risk_spread = max(risks) - min(risks)

    if risk_spread > 15.0:
        debate_points.append(
            f"Specialist Divergence: Risk estimates diverge by {risk_spread:.1f}% across disciplines. "
            f"Surgical focus on margin clearance ({op_surg.assessed_relapse_risk_pct}%) differs from "
            f"systemic ctDNA risk ({op_med.assessed_relapse_risk_pct}%)."
        )
    else:
        debate_points.append(
            f"Inter-Specialist Concordance: Consistent risk estimates across all disciplines (spread: {risk_spread:.1f}%)."
        )

    if history.procedures.surgical_margin in ["R1", "R2"]:
        debate_points.append(
            "Surgical vs. Radiation Priority: Positive margin (R1/R2) requires consensus on re-resection vs. targeted radiation boost."
        )

    if history.biomarkers.ctdna_status == "positive":
        debate_points.append(
            "Molecular MRD Escalation: Medical oncology emphasizes persistent ctDNA positivity over normal cross-sectional imaging."
        )

    action_plan = []
    for op in opinions:
        for item in op.recommended_interventions:
            if item not in action_plan:
                action_plan.append(item)

    if not action_plan:
        action_plan = [
            "Continue standard guideline surveillance imaging every 6 months for the next 2 years.",
            "Serial circulating biomarker monitoring (every 3 months).",
            "Maintain adherence to prescribed risk-reducing maintenance medications."
        ]

    # Rebuttal messages from Round 2
    r2_messages = [m for m in transcript if m.round_number == 2]
    r2_summary = "\n".join([f"- {m.speaker_role}: {m.content}" for m in r2_messages])
    evidence_text_block = "\n".join([f"- {e.title}: {e.excerpt} (HR: {e.hazard_ratio or 'N/A'})" for e in evidence])

    prompt = (
        f"You are the Tumor Board Supervisor Agent, presiding over the Multidisciplinary Virtual Tumor Board.\n"
        f"Patient Context: {history.stage_at_diagnosis} {history.primary_cancer_type}, {history.years_in_remission:.1f} years post-treatment.\n"
        f"- Current Medications: '{history.current_medications or 'None reported'}'.\n"
        f"- Surgical Margin: {history.procedures.surgical_margin}, Chemotherapy: {'Yes' if history.procedures.chemotherapy else 'No'}, Radiation: {'Yes' if history.procedures.radiation_therapy else 'No'}.\n"
        f"- Biomarkers: PSA={history.biomarkers.psa_ng_ml}, CEA={history.biomarkers.cea_ng_ml}, CA-125={history.biomarkers.ca125_u_ml}, ctDNA={history.biomarkers.ctdna_status}, Alterations={history.biomarkers.genomic_alterations or 'None'}.\n\n"
        f"Round 1 Opening Statements:\n"
        f"- Medical Oncology: '{op_med.reasoning}' ({op_med.assessed_relapse_risk_pct}%)\n"
        f"- Surgical Oncology: '{op_surg.reasoning}' ({op_surg.assessed_relapse_risk_pct}%)\n"
        f"- Radiation Oncology: '{op_rad.reasoning}' ({op_rad.assessed_relapse_risk_pct}%)\n\n"
        f"Round 2 Peer Rebuttals & Cross-Examination:\n{r2_summary}\n\n"
        f"- Weighted Consensus Relapse Risk: {consensus_relapse_risk}% ({risk_tier}).\n\n"
        f"Relevant Clinical Trials & Guideline Evidence:\n{evidence_text_block or 'Standard NCCN surveillance protocol applies.'}\n\n"
        f"Draft an authoritative, compassionate, 3-paragraph Tumor Board Adjudication Summary. "
        f"Directly synthesize the debate clash (ctDNA systemic prioritization vs. margin re-excision vs. SBRT boost), "
        f"confirm the final consensus risk of {consensus_relapse_risk}%, and declare the unified immediate management protocol. "
        f"Do not use fictional human names or academic degrees."
    )

    try:
        llm_summary = llm_client.generate(prompt)
        if not llm_summary or len(llm_summary.strip()) < 50:
            raise ValueError("Empty LLM output")
        adjudication_text = llm_summary.strip()
    except Exception:
        trial_cite = f" (supported by {evidence[0].title})" if evidence else ""
        adjudication_text = (
            f"The Multidisciplinary Virtual Tumor Board convened to review this {history.stage_at_diagnosis} {history.primary_cancer_type} "
            f"case at {history.years_in_remission:.1f} years of disease-free remission. Following deliberative analysis and direct specialist cross-examination, "
            f"the board established a consensus 5-year relapse probability of {consensus_relapse_risk}% ({risk_tier}){trial_cite}. "
            f"Medical oncology emphasized systemic micrometastatic risk and circulating biomarker kinetics, while surgical and radiation oncology "
            f"debated local margin status ({history.procedures.surgical_margin}) versus stereotactic field sterilization. "
            f"The panel recommends unified execution of the agreed surveillance and therapeutic action plan."
        )

    transcript.append(DebateMessage(
        round_number=3,
        round_title="Round 3: Multidisciplinary Consensus Adjudication",
        speaker_role="Tumor Board Supervisor Agent",
        speaker_name="Tumor Board Supervisor Agent",
        content=adjudication_text
    ))

    consensus_summary = (
        f"Multidisciplinary consensus established at {consensus_relapse_risk}% 5-year relapse risk ({risk_tier}). "
        f"Deliberated by Medical Oncology ({op_med.assessed_relapse_risk_pct}%), "
        f"Surgical Oncology ({op_surg.assessed_relapse_risk_pct}%), and "
        f"Radiation Oncology ({op_rad.assessed_relapse_risk_pct}%)."
    )

    traces.append(AgentTraceLog(
        agent_name="Tumor Board Supervisor Agent",
        step_title="Tumor Board Adjudication & Consensus Synthesis",
        details=f"Adjudicated 3 specialist opinions and 3 cross-rebuttals. Consensus 5-year relapse risk finalized at {consensus_relapse_risk}% ({risk_tier})."
    ))

    final_result = TumorBoardDebateResult(
        primary_cancer=history.primary_cancer_type or "Colorectal",
        stage=history.stage_at_diagnosis or "Stage II",
        consensus_relapse_risk_5yr_pct=consensus_relapse_risk,
        risk_tier=risk_tier,
        consensus_summary=consensus_summary,
        key_debate_points=debate_points,
        adjudication_rationale=adjudication_text,
        agent_opinions=opinions,
        action_plan=action_plan,
        debate_transcript=transcript,
        agent_traces=traces,
        evidence_citations=evidence
    )

    return {"final_result": final_result, "traces": traces, "transcript": transcript}

# Build LangGraph StateGraph
builder = StateGraph(TumorBoardDebateState)

# Add Nodes
builder.add_node("medical_oncology", medical_oncology_node)
builder.add_node("surgical_oncology", surgical_oncology_node)
builder.add_node("radiation_oncology", radiation_oncology_node)
builder.add_node("evidence_retrieval", evidence_retrieval_node)
builder.add_node("supervisor_adjudication", supervisor_adjudication_node)

# Flow Edges
builder.add_edge(START, "medical_oncology")
builder.add_edge("medical_oncology", "surgical_oncology")
builder.add_edge("surgical_oncology", "radiation_oncology")

# Cyclical Debate conditional edge:
# Round 1 -> routes back to medical_oncology for Round 2
# Round 2 -> routes forward to evidence_retrieval
builder.add_conditional_edges(
    "radiation_oncology",
    debate_router,
    {
        "advance_to_cross_rebuttal": "medical_oncology",
        "proceed_to_evidence": "evidence_retrieval"
    }
)

builder.add_edge("evidence_retrieval", "supervisor_adjudication")
builder.add_edge("supervisor_adjudication", END)

# Compile LangGraph
tumor_board_graph = builder.compile()

def run_tumor_board_debate(history: PriorCancerHistory) -> TumorBoardDebateResult:
    """Executes the compiled LangGraph Tumor Board debate."""
    initial_state: TumorBoardDebateState = {
        "history": history,
        "opinions": [],
        "traces": [],
        "transcript": [],
        "round_number": 1,
        "evidence": [],
        "final_result": None
    }
    final_state = tumor_board_graph.invoke(initial_state)
    return final_state["final_result"]
