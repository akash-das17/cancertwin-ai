import uuid
from typing import Dict, Any
from src.agents.base import BaseAgent
from src.models.patient import PatientProfile, DigitalTwinState
from src.utils.risk_calculators import calculate_health_score

class IntakeAgent(BaseAgent):
    """Agent responsible for ingesting, validating, and synthesizing raw patient records into a DigitalTwinState."""

    def __init__(self):
        super().__init__(
            name="Intake & Profiler Agent",
            role="Validates clinical inputs and normalizes patient data into a Digital Twin state vector"
        )

    def run(self, profile: PatientProfile) -> DigitalTwinState:
        self.clear_traces()
        self.log(
            step_title="Ingesting Clinical Profile",
            details=f"Received patient profile ID={profile.patient_id}, Age={profile.age}, Sex={profile.biological_sex}, Ancestry={profile.genetics.ancestry}."
        )

        # Calculate systemic health score using clinical deterministic formula
        score = calculate_health_score(profile)
        vulnerabilities = []

        # Smoking
        if profile.lifestyle.smoking_status == "current":
            vulnerabilities.append(f"High-impact tobacco exposure ({profile.lifestyle.pack_years:.1f} pack-years)")
            self.log(
                step_title="Lifestyle Risk Flag",
                details=f"Active tobacco use detected. Pack-years: {profile.lifestyle.pack_years:.1f}."
            )
        elif profile.lifestyle.smoking_status == "former":
            vulnerabilities.append(f"Former smoker ({profile.lifestyle.pack_years:.1f} pack-years)")

        # Genetics
        if profile.genetics.brca_mutation:
            vulnerabilities.append("Pathogenic BRCA1/2 genetic variant")
            self.log(
                step_title="Genomic Vulnerability Flag",
                details="BRCA pathogenic variant confirmed. Triggered heightened breast/prostate surveillance protocol."
            )
        if profile.genetics.lynch_syndrome:
            vulnerabilities.append("Lynch Syndrome (HNPCC) genetic mutation")
            self.log(
                step_title="Genomic Vulnerability Flag",
                details="Lynch syndrome identified. Colorectal and endometrial surveillance pathways engaged."
            )
        if profile.genetics.egfr_mutation:
            vulnerabilities.append("EGFR/KRAS oncogenic variant detected")

        # Environmental & Diet
        if profile.environmental.pm25_exposure_ug_m3 >= 35.0:
            vulnerabilities.append(f"High particulate air pollution ({profile.environmental.pm25_exposure_ug_m3:.1f} μg/m3)")
        if profile.environmental.residential_radon_risk == "high":
            vulnerabilities.append("High residential radon exposure zone")
        if profile.lifestyle.ultra_processed_food_pct >= 40.0:
            vulnerabilities.append("High ultra-processed dietary pattern (>40% caloric intake)")

        # Cervical / HPV status
        if profile.biological_sex.lower() == "female":
            if not profile.screening.hpv_vaccinated:
                vulnerabilities.append("Absence of high-risk HPV vaccination")
            if profile.screening.abnormal_pap_history:
                vulnerabilities.append("Documented history of abnormal cervical cytology")

        # Prostate status
        if profile.biological_sex.lower() == "male":
            if profile.genetics.ancestry == "african":
                vulnerabilities.append("African ancestry (higher baseline prostate cancer incidence/mortality)")
            if profile.screening.baseline_psa_ng_ml and profile.screening.baseline_psa_ng_ml >= 4.0:
                vulnerabilities.append(f"Elevated baseline PSA ({profile.screening.baseline_psa_ng_ml:.1f} ng/mL)")

        # Compile normalized state vector
        state_vector = {
            "age_norm": profile.age / 100.0,
            "bmi_norm": min(profile.lifestyle.bmi / 50.0, 1.0),
            "pack_years_norm": min(profile.lifestyle.pack_years / 60.0, 1.0),
            "alcohol_norm": min(profile.lifestyle.alcohol_drinks_per_week / 25.0, 1.0),
            "brca_flag": 1.0 if profile.genetics.brca_mutation else 0.0,
            "lynch_flag": 1.0 if profile.genetics.lynch_syndrome else 0.0,
            "pm25_norm": min(profile.environmental.pm25_exposure_ug_m3 / 100.0, 1.0),
            "exercise_norm": min(profile.lifestyle.physical_activity_hours_week / 10.0, 1.0),
            "med_diet_norm": profile.lifestyle.mediterranean_diet_score / 10.0,
            "hpv_vac_flag": 1.0 if profile.screening.hpv_vaccinated else 0.0
        }

        twin_id = f"TWIN-{uuid.uuid4().hex[:8].upper()}"
        digital_twin = DigitalTwinState(
            twin_id=twin_id,
            patient_profile=profile,
            overall_health_score=score,
            primary_cancer_vulnerabilities=vulnerabilities,
            state_vector=state_vector
        )

        self.log(
            step_title="Twin State Synthesis Complete",
            details=f"Digital Twin generated: {twin_id}. Overall Health Index: {digital_twin.overall_health_score}/100 with {len(vulnerabilities)} active vulnerability flags."
        )

        return digital_twin
