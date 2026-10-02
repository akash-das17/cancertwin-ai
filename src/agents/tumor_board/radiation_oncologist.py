from typing import Tuple
from src.models.oncology_history import PriorCancerHistory
from src.models.risk_report import TumorBoardAgentOpinion, AgentTraceLog
from src.utils.llm_client import get_llm_client

class RadiationOncologistAgent:
    """Evaluates radiation field sterilization, tumor antigen kinetics (PSA, CEA, CA-125), and surveillance imaging protocols."""

    def __init__(self):
        self.role_name = "Radiation Oncology Agent"
        self.specialist_name = "Radiation Oncology Agent"
        self.llm_client = get_llm_client()

    def evaluate(self, history: PriorCancerHistory) -> Tuple[TumorBoardAgentOpinion, AgentTraceLog]:
        cancer = history.primary_cancer_type or "Colorectal"
        stage = history.stage_at_diagnosis or "Stage II"
        rad = history.procedures.radiation_therapy
        markers = history.biomarkers
        adherent = history.preventive_surveillance_adherent

        stage_base_risk = {
            "Stage I": 9.0,
            "Stage II": 23.0,
            "Stage III": 45.0,
            "Stage IV": 75.0
        }.get(stage, 23.0)

        concerns = []
        interventions = []
        multiplier = 1.0

        # Radiotherapy evaluation
        if rad:
            multiplier *= 0.80
            concerns.append(f"Adjuvant radiation delivered to {history.procedures.radiation_site or 'target field'} providing local bed sterilization.")
        else:
            if history.procedures.surgical_margin in ["R1", "R2"]:
                multiplier *= 1.45
                concerns.append("Omission of radiation in the presence of positive surgical margins creates substantial unsterilized local relapse risk.")
                interventions.append("Urgent radiation oncology consultation for salvage external beam radiotherapy (EBRT) or stereotactic body radiation (SBRT).")
            else:
                concerns.append("Radiotherapy omitted; acceptable for clear-margin early-stage disease without high-risk histology.")

        # Biomarker kinetics analysis (Antigens)
        # PSA
        if markers.psa_ng_ml is not None:
            if markers.psa_ng_ml > 4.0:
                multiplier *= 1.60
                concerns.append(f"Elevated serum PSA ({markers.psa_ng_ml:.2f} ng/mL) suggests biochemical recurrence.")
                interventions.append("Initiate PSMA-PET/CT imaging to localize anatomical site of biochemical recurrence.")
            elif markers.psa_ng_ml > 0.2 and cancer.lower() == "prostate":
                multiplier *= 1.30
                concerns.append(f"Post-prostatectomy detectable PSA ({markers.psa_ng_ml:.2f} ng/mL) indicates impending biochemical failure.")
            else:
                concerns.append(f"Reassuring baseline serum PSA ({markers.psa_ng_ml:.2f} ng/mL).")

        # CEA
        if markers.cea_ng_ml is not None:
            if markers.cea_ng_ml > 5.0:
                multiplier *= 1.55
                concerns.append(f"Elevated CEA ({markers.cea_ng_ml:.1f} ng/mL) indicates occult hepatic or pulmonary relapse.")
                interventions.append("Perform contrast-enhanced tri-phase CT of chest/abdomen/pelvis and colonoscopy.")
            else:
                concerns.append(f"Normal surveillance CEA level ({markers.cea_ng_ml:.1f} ng/mL).")

        # CA-125
        if markers.ca125_u_ml is not None:
            if markers.ca125_u_ml > 35.0:
                multiplier *= 1.50
                concerns.append(f"Elevated CA-125 ({markers.ca125_u_ml:.1f} U/mL) raises high concern for peritoneal or nodal relapse.")
                interventions.append("Schedule pelvic MRI and diagnostic laparoscopy/PET.")

        # Surveillance adherence
        if not adherent:
            multiplier *= 1.25
            concerns.append("Non-adherent with recommended oncologic surveillance schedule, delaying early asymptomatic recurrence detection.")
            interventions.append("Strictly re-establish 3- to 6-month clinical oncology follow-up and surveillance imaging.")
        else:
            concerns.append("Patient is compliant with standard NCCN surveillance imaging and lab protocols.")

        years = history.years_in_remission
        remission_decay = max(0.40, 1.0 - (years * 0.13))
        final_risk = round(min(94.0, max(3.5, stage_base_risk * multiplier * remission_decay)), 1)

        # Agentic Cognitive Reasoning: Radiation Oncology Specialist Persona
        prompt = (
            f"You are the {self.specialist_name}, presenting your evaluation at a Multidisciplinary Virtual Tumor Board.\n"
            f"Patient Context: {stage} {cancer}, {years:.1f} years post-treatment remission.\n"
            f"- Radiotherapy Delivered: {'Yes (' + str(history.procedures.radiation_site or 'Target site') + ')' if rad else 'Omitted'}.\n"
            f"- Surgical Margin: {history.procedures.surgical_margin}.\n"
            f"- Circulating Biomarkers: PSA={markers.psa_ng_ml}, CEA={markers.cea_ng_ml}, CA-125={markers.ca125_u_ml}, ctDNA={markers.ctdna_status}.\n"
            f"- Surveillance Adherence: {'Strictly Adherent' if adherent else 'Lapsed / Non-adherent'}.\n"
            f"- Calculated Locoregional/Biomarker Baseline Risk: {final_risk}%.\n\n"
            f"In 2-3 concise, authoritative sentences in your professional clinical voice, state your radiation oncology assessment. "
            f"Address positive margins vs field coverage, tumor marker kinetics, and state your specific radiation or surveillance imaging recommendation. Do not use fictional human names or academic degrees."
        )

        try:
            llm_text = self.llm_client.generate(prompt)
            if llm_text and len(llm_text.strip()) > 30:
                reasoning = llm_text.strip()
            else:
                raise ValueError("Empty LLM output")
        except Exception:
            reasoning = (
                f"From a radiation and biomarker surveillance perspective, assessed relapse risk is {final_risk}%. "
                f"Key inputs include radiation field delivery ({'completed' if rad else 'none'}), "
                f"serum tumor markers (PSA={markers.psa_ng_ml}, CEA={markers.cea_ng_ml}, CA-125={markers.ca125_u_ml}), "
                f"and surveillance protocol adherence ({'adherent' if adherent else 'non-adherent'})."
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
            step_title="Radiation Field & Tumor Marker Surveillance Assessment",
            details=f"Assessed radiation status (RT={rad}), biomarkers (PSA={markers.psa_ng_ml}, CEA={markers.cea_ng_ml}), surveillance adherence={adherent}. Relapse risk evaluated at {final_risk}%."
        )

        return opinion, trace

    def cross_examine_and_rebut(
        self,
        history: PriorCancerHistory,
        med_opinion: TumorBoardAgentOpinion,
        surg_opinion: TumorBoardAgentOpinion
    ) -> str:
        """Round 2: Evaluates medical and surgical oncology assertions, offering stereotactic radiation and surveillance counter-arguments."""
        margin = history.procedures.surgical_margin
        ctdna = history.biomarkers.ctdna_status

        prompt = (
            f"You are the {self.specialist_name} at an active Tumor Board cross-debate.\n"
            f"Medical Oncology Agent argued: '{med_opinion.reasoning}' (Assessed risk: {med_opinion.assessed_relapse_risk_pct}%).\n"
            f"Surgical Oncology Agent argued: '{surg_opinion.reasoning}' (Assessed risk: {surg_opinion.assessed_relapse_risk_pct}%).\n"
            f"Patient margin is '{margin}', ctDNA status: '{ctdna}'.\n\n"
            f"Provide your radiation oncology cross-rebuttal. "
            f"If Surgical Oncology pushes for invasive re-excision, argue why stereotactic body radiotherapy (SBRT) or image-guided radiotherapy (IGRT) to the tumor bed provides equivalent local sterilization without surgical delay to systemic therapy. "
            f"If Medical Oncology wants to omit local therapy entirely for chemo/TKI, argue why gross/microscopic residual margins require definitive field sterilization to prevent seeding. "
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
                f"Surgical re-operation carries avoidable morbidity and risks delaying needed systemic therapies. "
                f"Image-guided stereotactic radiotherapy (SBRT) to the {margin} operative bed delivers definitive ablative doses with minimal tissue toxicity, "
                f"allowing concurrent or prompt initiation of systemic targeted agents."
            )
        return (
            f"Radiation oncology concurs that with clear surgical margins, focal radiotherapy is not indicated. "
            f"We advise adherence to serial imaging surveillance alongside medical oncology's circulating biomarker tracking."
        )

