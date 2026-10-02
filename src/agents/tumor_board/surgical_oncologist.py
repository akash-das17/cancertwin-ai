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
            f"In exactly 2 concise clinical sentences (under 40 words total), state your surgical assessment. "
            f"Focus on anatomic margin clearance, risk of local recurrence vs re-excision feasibility, and nodal surveillance. "
            f"CRITICAL: Do NOT use markdown asterisks (**), bolding, or fictional human names. Plain clinical text only."
        )

        from src.utils.llm_client import clean_markdown_artifacts

        try:
            llm_text = self.llm_client.generate(prompt, max_output_tokens=350)
            if llm_text and len(llm_text.strip()) > 20:
                reasoning = clean_markdown_artifacts(llm_text)
            else:
                raise ValueError("Empty LLM output")
        except Exception:
            reasoning = clean_markdown_artifacts(
                f"Surgical oncology assesses a locoregional recurrence risk of {final_risk}% based on {margin} surgical margin clearance. "
                f"Our anatomical priority is regional nodal surveillance with re-excision considered only if margins remain unsterilized."
            )

        opinion = TumorBoardAgentOpinion(
            agent_role=self.role_name,
            specialist_name=self.specialist_name,
            assessed_relapse_risk_pct=final_risk,
            reasoning=reasoning,
            key_concerns=[clean_markdown_artifacts(c) for c in concerns],
            recommended_interventions=[clean_markdown_artifacts(i) for i in interventions]
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
        from src.utils.llm_client import clean_markdown_artifacts
        margin = history.procedures.surgical_margin
        ctdna = history.biomarkers.ctdna_status

        prompt = (
            f"You are the {self.specialist_name} at an active Tumor Board cross-debate.\n"
            f"Medical Oncology Agent argued: '{med_opinion.reasoning}' (Assessed risk: {med_opinion.assessed_relapse_risk_pct}%).\n"
            f"Radiation Oncology Agent argued: '{rad_opinion.reasoning}' (Assessed risk: {rad_opinion.assessed_relapse_risk_pct}%).\n"
            f"Patient margin is '{margin}', ctDNA status: '{ctdna}'.\n\n"
            f"In exactly 1-2 brief sentences (under 30 words total), state your surgical cross-rebuttal. "
            f"State your position on margin control versus systemic delays. "
            f"CRITICAL: Do NOT use markdown asterisks (**) or bolding. Plain text only."
        )

        try:
            res = self.llm_client.generate(prompt, max_output_tokens=250)
            if res and len(res.strip()) > 20:
                return clean_markdown_artifacts(res)
        except Exception:
            pass

        if margin in ["R1", "R2"]:
            return clean_markdown_artifacts(
                f"Microscopically positive margins ({margin}) require definitive bed sterilization. "
                f"If re-excision is omitted to avoid systemic delays, targeted stereotactic radiation must be delivered."
            )
        return clean_markdown_artifacts(
            "With clear R0 surgical margins achieved, our primary anatomical objective is complete. "
            "We concur with prioritizing systemic surveillance and cross-sectional monitoring."
        )

