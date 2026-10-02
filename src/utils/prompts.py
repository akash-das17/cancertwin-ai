"""Prompt templates, LLM generation, and clinical narrative generators for CancerTwin AI agents."""
from typing import Dict, Any, List, Optional
from src.utils.llm_client import llm_client
from src.models.patient import PatientProfile
from src.models.risk_report import PreSimulationRecommendationItem

COORDINATOR_SYSTEM_PROMPT = """You are CancerTwin AI — an advanced Clinical Oncology Digital Twin coordinator.
Your objective is to synthesize concise, high-impact counterfactual What-If intervention projections.

Clinical Directives:
- Write in a brief, cohesive, single-paragraph clinical executive summary (under 75 words).
- Mention the primary baseline cancer vulnerability and modifiable risk reduction.
- Ground your recommendation in established oncology guidelines (USPSTF, NCCN, WCRF).
- CRITICAL: Never use markdown bolding asterisks (**) or bullet points. Output clean, continuous clinical text only.
"""

def build_pre_simulation_recommendations(profile: PatientProfile, assessments: dict) -> List[PreSimulationRecommendationItem]:
    """Generates concrete, guideline-grounded clinical action items immediately following patient profile intake."""
    recs: List[PreSimulationRecommendationItem] = []
    age = profile.age
    sex = profile.biological_sex.lower()
    genetics = profile.genetics
    lifestyle = profile.lifestyle
    env = profile.environmental
    screening = profile.screening

    # --- 1. Screening Recommendations ---
    # Cervical Screening
    if sex == "female" and 21 <= age <= 65:
        if screening.last_pap_smear_years_ago is None or screening.last_pap_smear_years_ago > 3.0:
            recs.append(PreSimulationRecommendationItem(
                category="Screening",
                title="Cervical Cytology & hrHPV Co-Testing",
                recommendation="Undergo cervical cytology alone every 3 years (ages 21-29) or high-risk HPV (hrHPV) co-testing every 5 years (ages 30-65).",
                guideline_source="USPSTF Grade A Recommendation",
                action_interval="Every 3 to 5 years",
                impact_estimate="Reduces invasive cervical cancer incidence by >80% through early identification and removal of HSIL/CIN2+ precancerous lesions.",
                url="https://pubmed.ncbi.nlm.nih.gov/30128532/"
            ))
        if not screening.hpv_vaccinated and age <= 45:
            recs.append(PreSimulationRecommendationItem(
                category="Screening",
                title="9-Valent Prophylactic HPV Catch-Up Vaccination",
                recommendation="Discuss 9-valent HPV vaccination (Gardasil 9) series with clinician to protect against oncogenic HPV types 16, 18, 31, 33, 45, 52, and 58.",
                guideline_source="CDC / ACIP Guidelines",
                action_interval="Immediate 2- or 3-dose series",
                impact_estimate="Confers up to 88% protective efficacy against HPV-driven cervical, anogenital, and oropharyngeal carcinomas.",
                url="https://www.cdc.gov/mmwr/volumes/68/wr/mm6832a3.htm"
            ))

    # Prostate Screening
    if sex == "male" and age >= 50:
        freq = "Every 1-2 years" if genetics.ancestry == "african" or any("prostate" in f.lower() for f in genetics.family_cancer_history) else "Every 2-4 years"
        recs.append(PreSimulationRecommendationItem(
            category="Screening",
            title="Shared Decision-Making Serum PSA & Digital Rectal Examination",
            recommendation="Engage in individualized shared decision-making regarding baseline serum PSA testing, with risk stratification based on family history and ancestry.",
            guideline_source="USPSTF Grade C / AUA Guidelines",
            action_interval=freq,
            impact_estimate="Reduces presentation with metastatic de novo prostate adenocarcinoma by approximately 25-30%.",
            url="https://pubmed.ncbi.nlm.nih.gov/29742721/"
        ))

    # Colorectal Screening
    if 45 <= age <= 75:
        recs.append(PreSimulationRecommendationItem(
            category="Screening",
            title="Colorectal Cancer Screening (Colonoscopy / FIT)",
            recommendation="Complete optical screening colonoscopy every 10 years or annual high-sensitivity Fecal Immunochemical Test (FIT).",
            guideline_source="USPSTF Grade A Recommendation",
            action_interval="Colonoscopy every 10 years (or annual FIT)",
            impact_estimate="Reduces colorectal cancer incidence and mortality by 50% to 68% via adenomatous polyp detection and polypectomy.",
            url="https://pubmed.ncbi.nlm.nih.gov/34003218/"
        ))

    # Lung Screening
    if 50 <= age <= 80 and (lifestyle.pack_years >= 20.0 or (lifestyle.smoking_status == "former" and (lifestyle.years_since_quitting or 0) <= 15)):
        recs.append(PreSimulationRecommendationItem(
            category="Screening",
            title="Low-Dose Chest CT (LDCT) Annual Screening",
            recommendation="Initiate annual low-dose computed tomography (LDCT) chest screening without contrast.",
            guideline_source="USPSTF Grade A Recommendation",
            action_interval="Annual",
            impact_estimate="Demonstrates 20% to 24% relative reduction in lung cancer mortality in heavy tobacco-exposed cohorts.",
            url="https://pubmed.ncbi.nlm.nih.gov/33683292/"
        ))

    # Breast Screening
    if sex == "female" and 40 <= age <= 74:
        recs.append(PreSimulationRecommendationItem(
            category="Screening",
            title="Biennial Screening Mammography (+/- Breast MRI if high risk)",
            recommendation="Undergo biennial digital breast tomosynthesis (3D mammography). If lifetime risk >= 20% or BRCA+, add annual contrast breast MRI.",
            guideline_source="USPSTF Grade B / NCCN Category 1",
            action_interval="Biennial (Annual if BRCA+)",
            impact_estimate="Reduces breast cancer-specific mortality by 19-22% via early identification of localized DCIS and Stage I lesions.",
            url="https://pubmed.ncbi.nlm.nih.gov/38687799/"
        ))

    # --- 2. Dietary Recommendations ---
    if lifestyle.dietary_fiber_grams_day < 25.0:
        recs.append(PreSimulationRecommendationItem(
            category="Dietary",
            title="Increase Dietary Fiber Intake to ≥30 Grams/Day",
            recommendation="Shift dietary composition to emphasize whole grains, legumes, chia seeds, and cruciferous vegetables to reach at least 30g daily fiber.",
            guideline_source="WCRF / AICR Strong Evidence",
            action_interval="Daily continuous",
            impact_estimate="Decreases colorectal adenocarcinoma risk by ~18% by accelerating fecal transit and promoting short-chain fatty acid (butyrate) colonic health.",
            url="https://www.wcrf.org/diet-and-cancer/colorectal-cancer/"
        ))

    if lifestyle.ultra_processed_food_pct >= 30.0 or lifestyle.red_processed_meat_servings_week >= 4.0:
        recs.append(PreSimulationRecommendationItem(
            category="Dietary",
            title="Eliminate Processed Meats & Restrict Ultra-Processed Foods",
            recommendation="Eliminate processed cured meats (bacon, cold cuts, hot dogs, classified as Group 1 carcinogens) and reduce ultra-processed foods to <15% of daily calories.",
            guideline_source="IARC Monographs / WCRF Guidelines",
            action_interval="Immediate lifestyle transition",
            impact_estimate="Attenuates colorectal and metabolic-linked oncogenesis by eliminating heterocyclic amines, polycyclic aromatic hydrocarbons, and nitrosamines.",
            url="https://www.iarc.who.int/news-events/iarc-monographs-evaluate-consumption-of-red-meat-and-processed-meat/"
        ))

    # --- 3. Environmental & Lifestyle Mitigations ---
    if env.pm25_exposure_ug_m3 >= 25.0:
        recs.append(PreSimulationRecommendationItem(
            category="Environmental",
            title="Indoor HEPA Air Filtration & Particulate Mitigation",
            recommendation="Install certified True-HEPA air purification units in primary living and sleeping areas to minimize inhalable PM2.5 micro-particulate load.",
            guideline_source="WHO / IARC Ambient Air Pollution Guidance",
            action_interval="Continuous residential filtration",
            impact_estimate="Reduces indoor particulate micro-toxin exposure by up to 50-70%, lowering pulmonary oxidative stress and systemic vascular inflammation.",
            url="https://www.iarc.who.int/news-events/iarc-outdoor-air-pollution-a-leading-environmental-cause-of-cancer-deaths/"
        ))

    if env.residential_radon_risk in ["moderate", "high"]:
        recs.append(PreSimulationRecommendationItem(
            category="Environmental",
            title="Residential Alpha-Track Radon Testing & Sub-Slab Mitigation",
            recommendation="Conduct an approved long-term (90-day) residential radon alpha-track measurement. If levels exceed EPA action threshold (4.0 pCi/L), install active soil depressurization.",
            guideline_source="EPA / CDC Radon Health Advisory",
            action_interval="Single test with active mitigation if >4 pCi/L",
            impact_estimate="Mitigates the #1 cause of lung cancer in non-smokers and halts multiplicative risk synergy with tobacco smoke.",
            url="https://www.epa.gov/radon/health-risk-radon"
        ))

    # --- 4. Genetic & Ancestry Guidance ---
    if genetics.brca_mutation or genetics.ancestry == "ashkenazi_jewish":
        recs.append(PreSimulationRecommendationItem(
            category="Genetic",
            title="Genetic Counseling & High-Risk Multigene Panel Testing",
            recommendation="Complete formal clinical cancer genetic counseling and multigene panel sequencing (BRCA1, BRCA2, PALB2, ATM, CHEK2).",
            guideline_source="NCCN Genetic/Familial High-Risk Guidelines",
            action_interval="Immediate referral",
            impact_estimate="Unlocks personalized risk-reducing options including intensive MRI surveillance, chemoprevention (SERMs), and risk-reducing surgery.",
            url="https://www.nccn.org/guidelines/guidelines-detail?category=2&id=1503"
        ))

    if genetics.other_genomic_alterations:
        recs.append(PreSimulationRecommendationItem(
            category="Genetic",
            title=f"Precision Genomic Surveillance & Actionable Alteration Tracking ({genetics.other_genomic_alterations})",
            recommendation=f"Consult molecular oncology for biomarker-directed therapeutic options and basket clinical trials targeting {genetics.other_genomic_alterations}.",
            guideline_source="NCCN Biomarkers Compendium / ESMO Precision Oncology",
            action_interval="Immediate molecular review",
            impact_estimate="Enables early consideration of targeted kinase inhibitors or immune-sensitizing protocols tailored to this somatic profile.",
            url="https://www.nccn.org/guidelines/guidelines-detail?category=1"
        ))

    return recs

from src.utils.llm_client import llm_client, clean_markdown_artifacts

def generate_clinical_narrative(patient_summary: dict, assessment_results: dict, interventions_applied: dict) -> str:
    """Generates an evidence-grounded clinical narrative using real-time LLM inference (with fallback)."""
    age = patient_summary.get("age", 50)
    sex = patient_summary.get("sex", "individual")
    
    highest_risk_cancer = None
    max_risk = -1.0
    for c_type, assess in assessment_results.items():
        if assess["baseline_risk_pct"] > max_risk:
            max_risk = assess["baseline_risk_pct"]
            highest_risk_cancer = c_type

    applied_actions = []
    if interventions_applied.get("smoking_cessation"):
        applied_actions.append("complete smoking cessation")
    if interventions_applied.get("target_bmi"):
        applied_actions.append(f"optimizing BMI to {interventions_applied['target_bmi']}")
    if interventions_applied.get("target_exercise_hours_week"):
        applied_actions.append(f"increasing aerobic exercise to {interventions_applied['target_exercise_hours_week']}h/wk")
    if interventions_applied.get("adhere_recommended_screening"):
        applied_actions.append("adhering to screening protocols")
    if interventions_applied.get("hpv_catchup_vaccine"):
        applied_actions.append("9-valent HPV catch-up vaccination")
    if interventions_applied.get("indoor_hepa_pm25_mitigation"):
        applied_actions.append("indoor HEPA particulate filtration")

    interventions_str = ", ".join(applied_actions) if applied_actions else "lifestyle optimization and routine surveillance"

    user_prompt = (
        f"Synthesize this oncology digital twin simulation into an actionable clinical recommendation (3-4 concise sentences, ~75-90 words):\n"
        f"- Patient: {age}-year-old {sex}, Health Index: {patient_summary.get('health_score', 80)}/100.\n"
        f"- Primary Vulnerability: {highest_risk_cancer.capitalize() if highest_risk_cancer else 'General'} cancer ({max_risk:.1f}% 10-year baseline risk).\n"
        f"- Simulated Interventions: {interventions_str}.\n"
        f"Provide an actionable clinical action plan: explain the projected risk attenuation, provide concrete lifestyle prescriptions (dietary targets, physical activity minimums, environmental mitigations), and specify the exact guideline-directed screening protocols (NCCN/USPSTF intervals).\n"
        f"CRITICAL: Do NOT use markdown asterisks (**), bolding, bullet points, or titles. Plain clinical text only."
    )

    try:
        llm_output = llm_client.generate(prompt=user_prompt, system_instruction=COORDINATOR_SYSTEM_PROMPT, max_output_tokens=450)
        if llm_output and len(llm_output.strip()) > 25:
            return clean_markdown_artifacts(llm_output)
    except Exception:
        pass

    narrative = (
        f"CancerTwin Profile for {age}-year-old {sex}: Baseline risk demonstrates primary vulnerability in {highest_risk_cancer} cancer ({max_risk:.1f}% 10-year risk). "
        f"Simulating {interventions_str} achieves decisive multi-organ risk attenuation in accordance with established oncology guidelines."
    )
    return clean_markdown_artifacts(narrative)
