from typing import Dict, Any, Optional
from src.agents.base import BaseAgent
from src.models.patient import DigitalTwinState
from src.models.risk_report import CancerRiskAssessment
from src.rag.retriever import OncologyRetriever
from src.utils.risk_calculators import (
    calculate_lung_risk,
    calculate_colorectal_risk,
    calculate_breast_risk,
    calculate_cervical_risk,
    calculate_prostate_risk,
    generate_risk_trajectory
)

class RiskAssessmentAgent(BaseAgent):
    """Agent that performs 5-cancer baseline risk assessment using clinical calculators and ChromaDB RAG."""

    def __init__(self, retriever: Optional[OncologyRetriever] = None):
        super().__init__(
            name="Clinical Risk Assessment Agent",
            role="Evaluates 5-cancer baseline risks using empirical formulas and ChromaDB evidence retrieval"
        )
        self.retriever = retriever or OncologyRetriever()

    def _determine_category(self, risk_pct: float, pop_avg: float) -> str:
        ratio = risk_pct / max(0.1, pop_avg)
        if ratio >= 2.5 or risk_pct >= 15.0:
            return "High"
        elif ratio >= 1.5 or risk_pct >= 5.0:
            return "Elevated"
        elif ratio >= 0.8:
            return "Moderate"
        else:
            return "Low"

    def run(self, twin_state: DigitalTwinState) -> Dict[str, CancerRiskAssessment]:
        self.clear_traces()
        profile = twin_state.patient_profile
        patient_summary = (
            f"Age {profile.age}, {profile.biological_sex}, smoking {profile.lifestyle.smoking_status} "
            f"({profile.lifestyle.pack_years} pack-yrs), BMI {profile.lifestyle.bmi}, "
            f"Ancestry {profile.genetics.ancestry}, PM2.5 {profile.environmental.pm25_exposure_ug_m3} ug/m3"
        )
        if profile.genetics.other_genomic_alterations:
            patient_summary += f", Somatic/Genomic Alteration: {profile.genetics.other_genomic_alterations}"

        genomic_note = f" with genomic alteration: {profile.genetics.other_genomic_alterations}" if profile.genetics.other_genomic_alterations else ""
        self.log(
            step_title="5-Cancer Risk Evaluation Triggered",
            details=f"Evaluating baseline risk for Twin {twin_state.twin_id} across Lung, Colorectal, Breast, Cervical, and Prostate domains{genomic_note}."
        )

        assessments = {}

        # 1. Lung Cancer Assessment
        lung_raw = calculate_lung_risk(profile)
        self.log(
            step_title="Querying ChromaDB for Lung & Environmental Guidelines",
            details="Retrieving USPSTF screening, particulate PM2.5, and tobacco hazard guidelines from vector store."
        )
        lung_evidence = self.retriever.get_risk_context_for_cancer("Lung", patient_summary)
        lung_category = self._determine_category(lung_raw["risk_pct"], lung_raw["population_average_pct"])
        lung_traj = generate_risk_trajectory(lung_raw["risk_pct"], lung_raw["risk_pct"], years=10)
        
        assessments["Lung"] = CancerRiskAssessment(
            cancer_type="Lung",
            baseline_risk_pct=lung_raw["risk_pct"],
            counterfactual_risk_pct=lung_raw["risk_pct"],
            absolute_risk_reduction_pct=0.0,
            relative_risk_reduction_pct=0.0,
            population_average_pct=lung_raw["population_average_pct"],
            risk_category=lung_category,
            key_drivers=lung_raw["key_drivers"],
            evidence_citations=lung_evidence,
            trajectory=lung_traj
        )

        # 2. Colorectal Cancer Assessment
        crc_raw = calculate_colorectal_risk(profile)
        self.log(
            step_title="Querying ChromaDB for Colorectal & Dietary Guidelines",
            details="Retrieving USPSTF CRC colonoscopy and WCRF dietary fiber/UPF evidence from vector store."
        )
        crc_evidence = self.retriever.get_risk_context_for_cancer("Colorectal", patient_summary)
        crc_category = self._determine_category(crc_raw["risk_pct"], crc_raw["population_average_pct"])
        crc_traj = generate_risk_trajectory(crc_raw["risk_pct"], crc_raw["risk_pct"], years=10)

        assessments["Colorectal"] = CancerRiskAssessment(
            cancer_type="Colorectal",
            baseline_risk_pct=crc_raw["risk_pct"],
            counterfactual_risk_pct=crc_raw["risk_pct"],
            absolute_risk_reduction_pct=0.0,
            relative_risk_reduction_pct=0.0,
            population_average_pct=crc_raw["population_average_pct"],
            risk_category=crc_category,
            key_drivers=crc_raw["key_drivers"],
            evidence_citations=crc_evidence,
            trajectory=crc_traj
        )

        # 3. Breast Cancer Assessment
        breast_raw = calculate_breast_risk(profile)
        breast_evidence = []
        if profile.biological_sex.lower() == "female":
            self.log(
                step_title="Querying ChromaDB for Breast Guidelines",
                details="Retrieving NCI Gail, Ashkenazi BRCA, and mammography guidelines from vector store."
            )
            breast_evidence = self.retriever.get_risk_context_for_cancer("Breast", patient_summary)

        breast_category = self._determine_category(breast_raw["risk_pct"], breast_raw["population_average_pct"])
        breast_traj = generate_risk_trajectory(breast_raw["risk_pct"], breast_raw["risk_pct"], years=10)

        assessments["Breast"] = CancerRiskAssessment(
            cancer_type="Breast",
            baseline_risk_pct=breast_raw["risk_pct"],
            counterfactual_risk_pct=breast_raw["risk_pct"],
            absolute_risk_reduction_pct=0.0,
            relative_risk_reduction_pct=0.0,
            population_average_pct=breast_raw["population_average_pct"],
            risk_category=breast_category,
            key_drivers=breast_raw["key_drivers"],
            evidence_citations=breast_evidence,
            trajectory=breast_traj
        )

        # 4. Cervical Cancer Assessment
        cerv_raw = calculate_cervical_risk(profile)
        cerv_evidence = []
        if profile.biological_sex.lower() == "female":
            self.log(
                step_title="Querying ChromaDB for Cervical & HPV Guidelines",
                details="Retrieving USPSTF cervical screening and CDC HPV vaccination evidence from vector store."
            )
            cerv_evidence = self.retriever.get_risk_context_for_cancer("Cervical", patient_summary)

        cerv_category = self._determine_category(cerv_raw["risk_pct"], cerv_raw["population_average_pct"])
        cerv_traj = generate_risk_trajectory(cerv_raw["risk_pct"], cerv_raw["risk_pct"], years=10)

        assessments["Cervical"] = CancerRiskAssessment(
            cancer_type="Cervical",
            baseline_risk_pct=cerv_raw["risk_pct"],
            counterfactual_risk_pct=cerv_raw["risk_pct"],
            absolute_risk_reduction_pct=0.0,
            relative_risk_reduction_pct=0.0,
            population_average_pct=cerv_raw["population_average_pct"],
            risk_category=cerv_category,
            key_drivers=cerv_raw["key_drivers"],
            evidence_citations=cerv_evidence,
            trajectory=cerv_traj
        )

        # 5. Prostate Cancer Assessment
        prost_raw = calculate_prostate_risk(profile)
        prost_evidence = []
        if profile.biological_sex.lower() == "male":
            self.log(
                step_title="Querying ChromaDB for Prostate & PSA Guidelines",
                details="Retrieving USPSTF Grade C PSA screening and African ancestry hazard evidence from vector store."
            )
            prost_evidence = self.retriever.get_risk_context_for_cancer("Prostate", patient_summary)

        prost_category = self._determine_category(prost_raw["risk_pct"], prost_raw["population_average_pct"])
        prost_traj = generate_risk_trajectory(prost_raw["risk_pct"], prost_raw["risk_pct"], years=10)

        assessments["Prostate"] = CancerRiskAssessment(
            cancer_type="Prostate",
            baseline_risk_pct=prost_raw["risk_pct"],
            counterfactual_risk_pct=prost_raw["risk_pct"],
            absolute_risk_reduction_pct=0.0,
            relative_risk_reduction_pct=0.0,
            population_average_pct=prost_raw["population_average_pct"],
            risk_category=prost_category,
            key_drivers=prost_raw["key_drivers"],
            evidence_citations=prost_evidence,
            trajectory=prost_traj
        )

        self.log(
            step_title="5-Cancer Baseline Assessment Complete",
            details=(
                f"Calculated baseline risks: Lung={lung_raw['risk_pct']}%, Colorectal={crc_raw['risk_pct']}%, "
                f"Breast={breast_raw['risk_pct']}%, Cervical={cerv_raw['risk_pct']}%, Prostate={prost_raw['risk_pct']}%."
            )
        )

        return assessments
