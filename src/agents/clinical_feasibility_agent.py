"""
Clinical Feasibility and Safety Agent (Merged Behavioral Critic & Contraindication Guardrail).
Evaluates patient lifestyle friction, comorbidity safety guardrails, and stages the intervention plan into Phase 1 / Phase 2.
"""
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
from src.agents.base import BaseAgent
from src.models.patient import PatientProfile
from src.models.simulation import InterventionParameters
from src.models.risk_report import AgentTraceLog
from src.tools.contraindication_tool import audit_contraindications_and_feasibility
from src.utils.llm_client import get_llm_client

class ClinicalFeasibilityReport(BaseModel):
    friction_score: int
    feasibility_tier: str
    staging_recommended: bool
    contraindications: List[str] = Field(default_factory=list)
    safety_warnings: List[str] = Field(default_factory=list)
    clinical_critique: str
    phase_1_plan: List[str] = Field(default_factory=list)
    phase_2_plan: List[str] = Field(default_factory=list)

class ClinicalFeasibilityAndSafetyAgent(BaseAgent):
    """
    Audits counterfactual cancer prevention plans for:
    1. Comorbidity contraindications and chemoprevention interactions.
    2. Behavioral adherence friction (flags unrealistic multi-factor changes).
    3. Staging into Phase 1 (Months 1–6) and Phase 2 (Months 6–12).
    """

    def __init__(self):
        super().__init__(
            name="Clinical Feasibility & Safety Agent",
            role="Audits comorbidity contraindications, evaluates behavioral friction, and stages lifestyle plans"
        )
        self.llm_client = get_llm_client()

    def run(
        self,
        profile: PatientProfile,
        interventions: InterventionParameters
    ) -> ClinicalFeasibilityReport:
        self.clear_traces()

        # Step 1: Execute deterministic safety & feasibility audit tool
        audit = audit_contraindications_and_feasibility(profile, interventions)

        self.log(
            step_title="Safety & Behavioral Feasibility Audit",
            details=(
                f"Friction score: {audit['feasibility_friction_score']}/10 ({audit['feasibility_tier']}). "
                f"Contraindications flagged: {len(audit['contraindications'])}, Warnings: {len(audit['safety_warnings'])}."
            )
        )

        # Step 2: Agentic LLM reasoning to generate clinical critique and personalized staging guidance
        prompt = (
            f"You are the Clinical Feasibility & Safety Agent reviewing a cancer prevention plan.\n"
            f"Patient Context: Age {profile.age}, {profile.biological_sex}, BMI {profile.lifestyle.bmi}, "
            f"Smoking: {profile.lifestyle.smoking_status} ({profile.lifestyle.pack_years} pack-years), "
            f"Physical Activity: {profile.lifestyle.physical_activity_hours_week} hrs/week.\n"
            f"Proposed Interventions:\n"
            f"- Smoking Cessation: {interventions.smoking_cessation}\n"
            f"- Target BMI: {interventions.target_bmi}\n"
            f"- Target Exercise: {interventions.target_exercise_hours_week} hrs/week\n"
            f"- Dietary Fiber: {interventions.target_fiber_grams_day} g/day\n"
            f"- UPF Target: {interventions.target_ultra_processed_food_pct}%\n"
            f"Tool Findings:\n"
            f"- Friction Score: {audit['feasibility_friction_score']}/10 ({audit['feasibility_tier']})\n"
            f"- Friction Drivers: {', '.join(audit['friction_factors']) if audit['friction_factors'] else 'None'}\n"
            f"- Contraindications: {', '.join(audit['contraindications']) if audit['contraindications'] else 'None'}\n\n"
            f"In 2-3 concise sentences in an expert behavioral and medical safety voice, state your clinical critique. "
            f"Highlight why a staged execution (Phase 1 vs Phase 2) prevents behavioral abandonment and protects patient safety. "
            f"Do not use fictional human names or academic degrees."
        )

        try:
            critique = self.llm_client.generate(prompt)
            if not critique or len(critique.strip()) < 30:
                raise ValueError("Empty LLM output")
            critique_text = critique.strip()
        except Exception:
            critique_text = (
                f"The proposed plan represents a transformative risk reduction but carries a friction score of {audit['feasibility_friction_score']}/10. "
                f"Attempting simultaneous nicotine cessation, rapid BMI reduction, and aggressive exercise escalation induces high relapse rates. "
                f"Staging interventions into Phase 1 (tobacco stabilization and baseline screenings) and Phase 2 (progressive metabolic consolidation) maximizes long-term adherence."
            )

        self.log(
            step_title="Behavioral Staging Plan Formulated",
            details=f"Phase 1 formulated with {len(audit['phase_1_actions'])} immediate actions; Phase 2 formulated with {len(audit['phase_2_actions'])} consolidation actions."
        )

        return ClinicalFeasibilityReport(
            friction_score=audit["feasibility_friction_score"],
            feasibility_tier=audit["feasibility_tier"],
            staging_recommended=audit["staging_recommended"],
            contraindications=audit["contraindications"],
            safety_warnings=audit["safety_warnings"],
            clinical_critique=critique_text,
            phase_1_plan=audit["phase_1_actions"],
            phase_2_plan=audit["phase_2_actions"]
        )
