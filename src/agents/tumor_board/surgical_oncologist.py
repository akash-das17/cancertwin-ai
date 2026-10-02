from typing import Tuple, Dict, Any, List
from src.models.oncology_history import PriorCancerHistory
from src.models.risk_report import TumorBoardAgentOpinion, AgentTraceLog
from src.utils.llm_client import get_llm_client

class SurgicalOncologistAgent:
    """Evaluates local surgical margins (R0 vs R1/R2), lymphadenectomy adequacy, and locoregional recurrence risk."""

    def __init__(self):
        self.role_name = "Surgical Oncology Agent"
        self.specialist_name = "Surgical Oncology Agent"
        self.llm_client = get_llm_client()

    def evaluate(self, history: PriorCancerHistory) -> Tuple[TumorBoardAgentOpinion, AgentTraceLog]:
        cancer = history.primary_cancer_type or "Colorectal"
        stage = history.stage_at_diagnosis or "Stage II"
        margin = history.procedures.surgical_margin.upper()
        surgery = history.procedures.surgery_performed

        stage_base_risk = {
            "Stage I": 8.0,
            "Stage II": 22.0,
            "Stage III": 44.0,
            "Stage IV": 72.0
        }.get(stage, 22.0)

        concerns = []
        interventions = []
        multiplier = 1.0

        if not surgery:
            multiplier *= 1.50
            concerns.append("Primary surgical resection was not performed; high likelihood of persistent local anatomical disease.")
            interventions.append("Evaluate surgical resectability, organ-preserving resection, or definitive ablation.")
        else:
            # Margin evaluation
            if margin == "R1":
                multiplier *= 1.85
                concerns.append("CRITICAL: Microscopically positive surgical margins (R1 resection) markedly elevate locoregional recurrence risk.")
                interventions.append("Consider re-excision surgery if anatomically feasible, or boost adjuvant radiotherapy to the tumor bed.")
            elif margin == "R2":
                multiplier *= 2.30
                concerns.append("CRITICAL: Macroscopic gross residual tumor (R2 resection) remaining at primary surgical site.")
                interventions.append("Urgent multidisciplinary surgical reassessment for debulking or palliative cytoreduction.")
            else:
                multiplier *= 0.85
                concerns.append("Negative surgical resection margins (R0) achieved with adequate microscopic clearance.")

        # Stage specific local anatomy concerns
        if stage in ["Stage III", "Stage IV"]:
            concerns.append("High nodal stage indicates prior lymphatic invasion beyond the primary organ capsule.")
            interventions.append("High-resolution cross-sectional imaging to monitor regional nodal basins.")

        years = history.years_in_remission
        remission_decay = max(0.40, 1.0 - (years * 0.14))
        final_risk = round(min(95.0, max(3.0, stage_base_risk * multiplier * remission_decay)), 1)

        # Agentic Cognitive Reasoning: Surgical Oncology Specialist Persona
        prompt = (
            f"You are the {self.specialist_name}, presenting your surgical oncology evaluation at a Multidisciplinary Virtual Tumor Board.\n"
            f"Patient Context: {stage} {cancer}, {years:.1f} years post-treatment remission.\n"
            f"- Surgery Performed: {'Yes' if surgery else 'No'}.\n"
            f"- Surgical Resection Margin: {margin} ({'Microscopically Positive' if margin == 'R1' else 'Macroscopic Residual' if margin == 'R2' else 'Clear Margins'}).\n"
            f"- Calculated Locoregional Risk Baseline: {final_risk}%.\n\n"
            f"In 2-3 concise, authoritative sentences in your professional surgical voice, state your operative assessment. "
            f"Focus on anatomic margin clearance, risk of local tumor bed recurrence vs re-excision feasibility, and regional nodal surveillance. Do not use fictional human names or academic degrees."
        )

        try:
            llm_text = self.llm_client.generate(prompt)
            if llm_text and len(llm_text.strip()) > 30:
                reasoning = llm_text.strip()
            else:
                raise ValueError("Empty LLM output")
        except Exception:
            reasoning = (
                f"From a surgical and pathology standpoint, local recurrence probability is {final_risk}%. "
                f"The primary operative determinant is margin clearance ({margin}), alongside surgical completion ({'performed' if surgery else 'unperformed'}) "
                f"and regional lymphatic burden associated with {stage} {cancer}."
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
            step_title="Locoregional & Margin Clearance Analysis",
            details=f"Assessed operative resection status: surgery={surgery}, margin={margin}, stage={stage}. Local relapse risk evaluated at {final_risk}%."
        )

        return opinion, trace

    def cross_examine_and_rebut(
        self,
        history: PriorCancerHistory,
        med_opinion: TumorBoardAgentOpinion,
        rad_opinion: TumorBoardAgentOpinion
    ) -> str:
        """Round 2: Directly evaluates medical and radiation oncology positions and provides surgical counter-arguments."""
        margin = history.procedures.surgical_margin
        ctdna = history.biomarkers.ctdna_status

        prompt = (
            f"You are the {self.specialist_name} at an active Tumor Board cross-debate.\n"
            f"Medical Oncology Agent argued: '{med_opinion.reasoning}' (Assessed risk: {med_opinion.assessed_relapse_risk_pct}%).\n"
            f"Radiation Oncology Agent argued: '{rad_opinion.reasoning}' (Assessed risk: {rad_opinion.assessed_relapse_risk_pct}%).\n"
            f"Patient margin is '{margin}', ctDNA status: '{ctdna}'.\n\n"
            f"Provide your surgical cross-rebuttal. "
            f"If margin is R1/R2, defend why leaving macroscopic or microscopic tumor cells in the operative bed creates a hypoxic sanctuary site that systemic chemotherapy alone cannot sterilize. "
            f"Explain whether re-excision is technically achievable or if radiation tumor bed boost is acceptable to avoid surgical morbidity. "
            f"Speak directly and authoritatively in 2-3 sentences. Do not use fictional human names or degrees."
        )

        try:
            res = self.llm_client.generate(prompt)
            if res and len(res.strip()) > 30:
                return res.strip()
        except Exception:
            pass

        if margin in ["R1", "R2"]:
            return (
                f"Microscopically positive margins ({margin}) cannot simply be ignored in favor of systemic therapy. "
                f"Residual tumor beds are poorly vascularized and create a sanctuary site where clonal resistance emerges. "
                f"If re-excision is omitted to avoid systemic therapy delays, high-dose stereotactic radiation bed boost must be guaranteed."
            )
        return (
            f"With clear R0 surgical margins achieved, our primary anatomical objective is complete. "
            f"We concur with prioritizing systemic surveillance and non-invasive cross-sectional monitoring of regional basins."
        )

