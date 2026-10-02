from typing import Dict, Any, List
from src.models.metastasis import MetastasisAnalysisRequest, MetastasisAnalysisResponse

# Seed-and-soil organotropism affinity lookup matrix (0.05 to 0.95)
ORGANOTROPISM_MATRIX: Dict[str, Dict[str, float]] = {
    "Colorectal": {
        "Liver": 0.88,
        "Lungs": 0.48,
        "Peritoneum": 0.52,
        "Bone": 0.15,
        "Brain": 0.05,
        "Pelvic Nodes": 0.60
    },
    "Breast": {
        "Bone": 0.85,
        "Lungs": 0.52,
        "Liver": 0.48,
        "Brain": 0.38,
        "Peritoneum": 0.12,
        "Pelvic Nodes": 0.25
    },
    "Lung": {
        "Brain": 0.78,
        "Bone": 0.55,
        "Adrenals": 0.62,
        "Liver": 0.45,
        "Peritoneum": 0.08,
        "Pelvic Nodes": 0.15
    },
    "Prostate": {
        "Bone": 0.92,
        "Pelvic Nodes": 0.70,
        "Lungs": 0.22,
        "Liver": 0.18,
        "Brain": 0.04,
        "Peritoneum": 0.05
    },
    "Cervical": {
        "Pelvic Nodes": 0.75,
        "Lungs": 0.45,
        "Liver": 0.28,
        "Bone": 0.22,
        "Brain": 0.05,
        "Peritoneum": 0.35
    },
    "Melanoma": {
        "Brain": 0.68,
        "Lungs": 0.62,
        "Liver": 0.45,
        "Bone": 0.35,
        "Pelvic Nodes": 0.40,
        "Peritoneum": 0.20
    }
}

TRAVEL_ROUTES: Dict[str, Dict[str, str]] = {
    "Colorectal": {
        "Liver": "Mesenteric venous drainage through the portal venous system directly seeds the hepatic sinusoidal capillary beds.",
        "Lungs": "Hematogenous escape via hepatic veins into the inferior vena cava and pulmonary microvasculature, or via lower rectal venous plexus (internal iliac veins).",
        "Peritoneum": "Direct transmural serosal invasion with peritoneal exfoliative seeding across the abdominal cavity."
    },
    "Breast": {
        "Bone": "Endocrine-mediated vascular dissemination with high CXCR4-CXCL12 bone marrow niche homing and osteolytic microenvironment colonisation.",
        "Brain": "Hematogenous arterial transit breaching the blood-brain barrier, characteristically observed in HER2+ and triple-negative subtypes.",
        "Lungs": "Systemic venous drainage via subclavian veins into the pulmonary arterial tree."
    },
    "Lung": {
        "Brain": "Direct arterial systemic dissemination from pulmonary veins into the left atrium and carotid circulation, circumventing the hepatic/pulmonary capillary filters.",
        "Bone": "Arterial hematogenous dissemination to the axial and appendicular skeleton.",
        "Adrenals": "Rich microvascular arterial perfusion of adrenal cortical beds providing fertile soil for bronchogenic metastases."
    },
    "Prostate": {
        "Bone": "Retrograde hematogenous migration via Batson's valveless paravertebral venous plexus under elevated intra-abdominal pressures.",
        "Pelvic Nodes": "Initial lymphatic dissemination along internal, external, and common iliac nodal basins."
    },
    "Cervical": {
        "Pelvic Nodes": "Stepwise lymphatic invasion from paracervical/obturator nodes to internal/external iliac and para-aortic chains.",
        "Lungs": "Hematogenous spread from thoracic duct drainage into the left subclavian vein and pulmonary microcirculation."
    }
}

def analyze_metastasis_vs_second_primary(req: MetastasisAnalysisRequest) -> MetastasisAnalysisResponse:
    """Evaluates whether a new lesion in another anatomical site is metastatic recurrence or a de novo second primary."""
    primary = req.prior_primary_cancer.capitalize()
    target = req.new_lesion_site.capitalize()
    dfi = req.disease_free_interval_years

    # 1. Base organotropism biological affinity
    matrix_for_primary = ORGANOTROPISM_MATRIX.get(primary, {})
    # Match fuzzy site
    matched_target = None
    for k in matrix_for_primary.keys():
        if k.lower() in target.lower() or target.lower() in k.lower():
            matched_target = k
            break
    
    if matched_target:
        organotropism_score = matrix_for_primary[matched_target]
    else:
        organotropism_score = 0.20  # Atypical metastatic site

    # Travel route explanation
    routes_for_primary = TRAVEL_ROUTES.get(primary, {})
    travel_route_mechanism = routes_for_primary.get(
        matched_target or target,
        f"Hematogenous or lymphatic vascular dissemination from primary {primary} site to {target}."
    )

    # 2. Disease-Free Interval (DFI) Latency Curve Modeling
    # Tumors recurring within 2-3 years are predominantly metastatic.
    # Tumors after 10 years are predominantly second primary, unless ER+ Breast or Melanoma.
    if dfi <= 2.0:
        dfi_metastatic_weight = 0.90
        dfi_assessment = f"Early relapse window ({dfi:.1f} years post-therapy): Clonal kinetic models indicate high probability of awakening occult micrometastases."
    elif dfi <= 5.0:
        dfi_metastatic_weight = 0.72
        dfi_assessment = f"Intermediate surveillance window ({dfi:.1f} years): Consistent with standard metastatic recurrence trajectory for {primary} cancer."
    elif dfi <= 10.0:
        # ER+ breast cancer has late recurrence risk
        if primary == "Breast":
            dfi_metastatic_weight = 0.55
            dfi_assessment = f"Late window ({dfi:.1f} years): Hormone-receptor positive breast cancer is known for delayed dormant bone/visceral recurrence up to 15-20 years."
        else:
            dfi_metastatic_weight = 0.35
            dfi_assessment = f"Prolonged latency ({dfi:.1f} years): Significantly favors an independent second primary malignancy over delayed dormant relapse."
    else:
        if primary == "Breast":
            dfi_metastatic_weight = 0.38
        else:
            dfi_metastatic_weight = 0.15
        dfi_assessment = f"Very late interval ({dfi:.1f} years): Strong epidemiological presumption of a de novo second primary cancer."

    # 3. Tumor Marker & ctDNA somatic concordances
    marker_multiplier = 1.0
    if req.elevated_primary_marker:
        marker_multiplier += 0.25
    if req.ctdna_positive:
        marker_multiplier += 0.30

    # 4. Compute composite probability
    # Composite formula balancing organotropism, latency, and biomarkers
    raw_metastasis_prob = (0.50 * dfi_metastatic_weight + 0.50 * organotropism_score) * marker_multiplier

    # Prior radiation field secondary malignancy factor
    radiation_risk_note = "No radiation field overlap noted."
    if req.prior_radiation_field and req.prior_radiation_field.lower() in target.lower():
        if dfi >= 5.0:
            raw_metastasis_prob -= 0.15  # Elevates second primary probability due to radiation-induced carcinogenesis
            radiation_risk_note = f"Prior radiotherapy to {req.prior_radiation_field} with >5-year latency confers heightened risk of radiation-associated secondary malignancy (e.g., sarcoma, secondary epithelial tumor)."
        else:
            radiation_risk_note = f"Prior radiotherapy field overlap observed, though latency ({dfi:.1f} yrs) is relatively short for classic radiation-induced secondary carcinogenesis."

    # Bound and normalize to 100%
    clamped_met = max(0.05, min(0.95, raw_metastasis_prob))
    metastasis_pct = round(clamped_met * 100.0, 1)
    second_primary_pct = round(100.0 - metastasis_pct, 1)

    # 5. Diagnostic recommendations & molecular confirmation panel
    workup = [
        f"Image-guided core needle biopsy of the {target} lesion for definitive histological and molecular subtyping.",
        "Comprehensive Next-Generation Sequencing (NGS) to compare somatic mutation profiles with archival primary specimen.",
        "PET-CT whole-body staging scan to exclude multi-focal systemic dissemination."
    ]

    molecular_markers = []
    if primary == "Colorectal":
        molecular_markers = ["CK7- / CK20+ / CDX2+ (Colorectal immunophenotype)", "KRAS/NRAS/BRAF concordant mutation status", "MSI/MMR status"]
    elif primary == "Breast":
        molecular_markers = ["GATA3+, Mammaglobin+, GCDFP-15+", "ER / PR / HER2 receptor discordance reassessment", "PIK3CA / ESR1 mutation panel"]
    elif primary == "Lung":
        molecular_markers = ["TTF-1+, Napsin A+ (Adenocarcinoma) or p40+ (Squamous)", "EGFR, ALK, ROS1, PD-L1 comparative concordance"]
    elif primary == "Prostate":
        molecular_markers = ["NKX3.1+, PSA+, PSMA+ immunohistochemistry", "TMPRSS2-ERG fusion concordance"]
    elif primary == "Cervical":
        molecular_markers = ["p16INK4a strong diffuse positivity", "HPV DNA / RNA in situ hybridization"]
    else:
        molecular_markers = ["Broad immunohistochemistry panel (CK7, CK20, S100, SOX10, AE1/AE3)", "Comparative somatic oncogenomics"]

    return MetastasisAnalysisResponse(
        prior_primary=primary,
        new_lesion_site=target,
        disease_free_interval_years=dfi,
        metastasis_probability_pct=metastasis_pct,
        second_primary_probability_pct=second_primary_pct,
        organotropism_score=round(organotropism_score, 2),
        organotropism_explanation=f"Biological organotropism affinity score is {organotropism_score:.2f}/1.00 for {primary} migrating to {target}.",
        travel_route_mechanism=travel_route_mechanism,
        dfi_latency_assessment=dfi_assessment,
        radiation_secondary_risk=radiation_risk_note,
        recommended_diagnostic_workup=workup,
        molecular_confirmation_markers=molecular_markers
    )
