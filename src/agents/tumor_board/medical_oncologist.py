from typing import Tuple, Dict, Any, List
from src.models.oncology_history import PriorCancerHistory
from src.models.risk_report import TumorBoardAgentOpinion, AgentTraceLog
from src.utils.llm_client import get_llm_client

class MedicalOncologistAgent:
    """Evaluates systemic relapse risk, adjuvant chemotherapy adequacy, immunotherapy response, and ctDNA persistence."""

    def __init__(self):
        self.role_name = "Medical Oncology Agent"
        self.specialist_name = "Medical Oncology Agent"
        self.llm_client = get_llm_client()

    def evaluate(self, history: PriorCancerHistory) -> Tuple[TumorBoardAgentOpinion, AgentTraceLog]:
        cancer = history.primary_cancer_type or "Colorectal"
        stage = history.stage_at_diagnosis or "Stage II"
        ctdna = history.biomarkers.ctdna_status.lower()
        chemo = history.procedures.chemotherapy
        t_cell = history.procedures.t_cell_immunotherapy
        meds = history.current_medications or "None reported"
        genomics = history.biomarkers.genomic_alterations

        # Baseline risk based on Stage (Deterministic Mathematical Tool)
        stage_base_risk = {
            "Stage I": 10.0,
            "Stage II": 24.0,
            "Stage III": 48.0,
            "Stage IV": 78.0
        }.get(stage, 25.0)

        concerns = []
        interventions = []
        multiplier = 1.0

        # ctDNA Impact (Key systemic biomarker)
        if ctdna == "positive":
            multiplier *= 1.65
            concerns.append("Persistent circulating tumor DNA (ctDNA) indicates residual microscopic disease.")
            interventions.append("Escalate systemic therapy; prioritize adjuvant targeted kinase inhibitor or chemotherapy.")
        elif ctdna == "negative":
            multiplier *= 0.70
            concerns.append("Negative/undetected ctDNA is reassuring for minimal residual disease absence.")
        else:
            concerns.append("ctDNA status is unknown; recommended to obtain liquid biopsy for MRD monitoring.")
            interventions.append("Order tumor-informed circulating tumor DNA assay (e.g., Signatera).")

        # Chemotherapy status
        if stage in ["Stage II", "Stage III", "Stage IV"]:
            if chemo:
                multiplier *= 0.75
                concerns.append(f"Received systemic chemotherapy ({history.procedures.chemotherapy_details or 'Adjuvant regimen'}).")
            else:
                multiplier *= 1.35
                concerns.append(f"Omission of systemic adjuvant chemotherapy in {stage} setting elevates distant metastatic hazard.")
                interventions.append("Evaluate candidacy for delayed systemic chemotherapy or maintenance targeted therapy.")

        # T-cell / Immunotherapy
        if t_cell:
            multiplier *= 0.85
            concerns.append("T-cell checkpoint immunotherapy administered conferring durable anti-tumor surveillance.")

        # Genomic alteration consideration
        if genomics:
            concerns.append(f"Actionable oncogenic driver alteration identified: {genomics}.")
            interventions.append(f"Evaluate targeted therapy protocol matched to {genomics}.")

        # Current medications check
        if any(w in meds.lower() for w in ["tamoxifen", "letrozole", "anastrozole", "aspirin", "capecitabine", "metformin"]):
            multiplier *= 0.90
            concerns.append(f"Active risk-reducing maintenance medication regimen: '{meds}'.")
        else:
            concerns.append(f"Current reported medications: '{meds}'.")

        # Remission decay (each disease-free year reduces annual hazard)
        years = history.years_in_remission
        remission_decay = max(0.40, 1.0 - (years * 0.12))
        final_risk = round(min(92.0, max(4.0, stage_base_risk * multiplier * remission_decay)), 1)

        # Agentic Cognitive Reasoning: Medical Oncology Specialist Persona
        prompt = (
            f"You are the {self.specialist_name}, presenting your evaluation at a Multidisciplinary Virtual Tumor Board.\n"
            f"Patient Context: {stage} {cancer}, {years:.1f} years post-treatment remission.\n"
            f"- Chemotherapy: {'Delivered (' + str(history.procedures.chemotherapy_details or 'Adjuvant') + ')' if chemo else 'Omitted'}.\n"
            f"- Immunotherapy: {'Yes' if t_cell else 'No'}.\n"
            f"- ctDNA Minimal Residual Disease: {ctdna.upper()}.\n"
            f"- Current Medications: '{meds}'.\n"
            f"- Genomic Alterations: '{genomics or 'None reported'}'.\n"
            f"- Calculated Systemic Hazard Baseline: {final_risk}%.\n\n"
            f"In 2-3 concise, authoritative sentences in your professional clinical voice, state your medical oncology evaluation. "
            f"Address systemic micrometastatic risk based on ctDNA kinetics and specify your targeted systemic recommendation. Do not use any fictional human names or academic degrees."
        )

        try:
            llm_text = self.llm_client.generate(prompt)
            if llm_text and len(llm_text.strip()) > 30:
                reasoning = llm_text.strip()
            else:
                raise ValueError("Empty LLM output")
        except Exception:
            reasoning = (
                f"From a medical oncology perspective, this {stage} {cancer} presentation carries a calculated 5-year systemic relapse risk of {final_risk}%. "
                f"Key systemic prognostic variables include circulating ctDNA status ({ctdna}), chemotherapy delivery ({'completed' if chemo else 'omitted'}), "
                f"and an ongoing disease-free interval of {years:.1f} years."
            )

        opinion = TumorBoardAgentOpinion(
            agent_role=self.role_name,
            specialist_name=self.specialist_name,
            assessed_relapse_risk_pct=final_risk,
            reasoning=reasoning,
            key_concerns=concerns,
            recommended_interventions=interventions
        )

        trace = AgentTraceLog(
            agent_name=self.role_name,
            step_title="Systemic & Micrometastatic Risk Stratification",
            details=f"Evaluated {stage} {cancer}. Assessed relapse hazard at {final_risk}% based on ctDNA={ctdna}, chemo={chemo}, meds='{meds}'."
        )

        return opinion, trace

    def cross_examine_and_rebut(
        self,
        history: PriorCancerHistory,
        surg_opinion: TumorBoardAgentOpinion,
        rad_opinion: TumorBoardAgentOpinion
    ) -> str:
        """Round 2: Directly reviews surgical and radiation arguments and provides an unvarnished cross-rebuttal."""
        ctdna = history.biomarkers.ctdna_status.lower()
        margin = history.procedures.surgical_margin
        genomics = history.biomarkers.genomic_alterations or "None"

        prompt = (
            f"You are the {self.specialist_name} at an active Tumor Board cross-debate.\n"
            f"Surgical Oncology Agent argued: '{surg_opinion.reasoning}' (Assessed risk: {surg_opinion.assessed_relapse_risk_pct}%, Concerns: {surg_opinion.key_concerns}).\n"
            f"Radiation Oncology Agent argued: '{rad_opinion.reasoning}' (Assessed risk: {rad_opinion.assessed_relapse_risk_pct}%).\n"
            f"Patient has ctDNA status: '{ctdna}' and surgical margin: '{margin}', alteration: '{genomics}'.\n\n"
            f"Provide your direct cross-examination rebuttal to Surgical and Radiation Oncology. "
            f"If Surgical Oncology advocates re-operation for positive margins while ctDNA is positive, challenge them on why delaying systemic therapy for wound healing carries lethal micrometastatic risk. "
            f"Speak directly and authoritatively in 2-3 sentences. Do not use fictional human names or degrees."
        )

        try:
            res = self.llm_client.generate(prompt)
            if res and len(res.strip()) > 30:
                return res.strip()
        except Exception:
            pass

        if ctdna == "positive" and margin in ["R1", "R2"]:
            return (
                f"Surgical re-excision of the {margin} margin must not take priority over systemic control when ctDNA is actively positive. "
                f"Re-operation imposes an 8-week wound healing recovery window during which untreated systemic micrometastases will progress. "
                f"Immediate systemic targeted therapy must take precedence, with margin control addressed via non-invasive stereotactic radiation boost."
            )
        return (
            f"From the systemic perspective, our primary therapeutic window is targeting circulating micrometastases before radiological relapse occurs. "
            f"Local modalities must be sequenced to avoid interrupting or delaying systemic therapeutic coverage."
        )

