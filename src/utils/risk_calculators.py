import math
from typing import List, Dict, Any
from src.models.patient import PatientProfile
from src.models.risk_report import RiskTrajectoryPoint

def calculate_lung_risk(profile: PatientProfile) -> Dict[str, Any]:
    """Calculates 10-year baseline lung cancer risk based on age, smoking, environmental PM2.5/radon, and genetics."""
    age = profile.age
    lifestyle = profile.lifestyle
    env = profile.environmental
    genetics = profile.genetics

    pack_years = lifestyle.pack_years
    smoking_status = lifestyle.smoking_status
    years_quit = lifestyle.years_since_quitting or 0.0

    # Age baseline risk for non-smoker (SEER 10-year probability)
    if age < 45:
        base_rate = 0.2
    elif age < 55:
        base_rate = 0.6
    elif age < 65:
        base_rate = 1.4
    elif age < 75:
        base_rate = 2.8
    else:
        base_rate = 3.5

    key_drivers = []
    multiplier = 1.0

    # Smoking excess risk
    if smoking_status == "current":
        smoker_multiplier = 1.0 + (pack_years * 0.35)
        multiplier *= smoker_multiplier
        key_drivers.append(f"Current smoker with {pack_years:.1f} pack-years")
    elif smoking_status == "former":
        decay_factor = math.exp(-0.08 * years_quit)
        smoker_multiplier = 1.0 + (pack_years * 0.35 * decay_factor)
        multiplier *= smoker_multiplier
        key_drivers.append(f"Former smoker ({pack_years:.1f} pack-years, quit {years_quit:.1f} yrs ago)")
    else:
        key_drivers.append("Non-smoker")

    # Environmental: PM2.5 air pollution (WHO/IARC Group 1)
    if env.pm25_exposure_ug_m3 >= 50.0:
        multiplier *= 1.35
        key_drivers.append(f"High ambient PM2.5 pollution exposure ({env.pm25_exposure_ug_m3:.1f} μg/m3)")
    elif env.pm25_exposure_ug_m3 >= 25.0:
        multiplier *= 1.18
        key_drivers.append(f"Moderate ambient PM2.5 exposure ({env.pm25_exposure_ug_m3:.1f} μg/m3)")

    # Environmental: Residential Radon
    if env.residential_radon_risk == "high":
        multiplier *= 1.30 if smoking_status == "never" else 1.50
        key_drivers.append("High residential radon zone exposure (synergistic carcinogenicity)")
    elif env.residential_radon_risk == "moderate":
        multiplier *= 1.12

    # Occupational carcinogens
    if env.occupational_carcinogen_exposure:
        multiplier *= 1.25
        key_drivers.append("Occupational exposure to asbestos, silica, or industrial solvents")

    # Family history factor
    family_lung = any("lung" in f.lower() for f in genetics.family_cancer_history)
    if family_lung:
        multiplier *= 1.40
        key_drivers.append("First-degree relative with lung cancer")

    # Genetic / Ancestry predisposition (e.g., East Asian non-smoker EGFR vulnerability)
    if genetics.egfr_mutation:
        multiplier *= 2.20
        key_drivers.append("Carrier of EGFR/KRAS oncogenic variant")
    elif genetics.ancestry == "east_asian" and smoking_status == "never":
        multiplier *= 1.25
        key_drivers.append("East Asian lineage (higher population prevalence of EGFR adenocarcinoma)")

    risk_pct = min(50.0, base_rate * multiplier)
    
    return {
        "risk_pct": round(risk_pct, 2),
        "population_average_pct": round(base_rate * 1.5, 2),
        "key_drivers": key_drivers
    }

def calculate_colorectal_risk(profile: PatientProfile) -> Dict[str, Any]:
    """Calculates 10-year colorectal cancer risk based on age, genetics, dietary habits, and metabolic lifestyle."""
    age = profile.age
    genetics = profile.genetics
    lifestyle = profile.lifestyle

    # Age base rate
    if age < 45:
        base_rate = 0.3
    elif age < 55:
        base_rate = 0.9
    elif age < 65:
        base_rate = 1.8
    else:
        base_rate = 2.5

    multiplier = 1.0
    key_drivers = []

    # Genetics (Lynch syndrome has high penetrance)
    if genetics.lynch_syndrome:
        multiplier *= 5.5
        key_drivers.append("High penetrance: Lynch Syndrome (HNPCC) positive")
    
    family_crc = any("colorectal" in f.lower() or "colon" in f.lower() for f in genetics.family_cancer_history)
    if family_crc:
        multiplier *= 1.80
        key_drivers.append("First-degree family history of colorectal cancer")

    # Lifestyle: BMI
    if lifestyle.bmi >= 30:
        multiplier *= 1.35
        key_drivers.append(f"Elevated BMI ({lifestyle.bmi:.1f})")
    elif lifestyle.bmi >= 25:
        multiplier *= 1.15

    # Lifestyle: Alcohol
    if lifestyle.alcohol_drinks_per_week >= 14:
        multiplier *= 1.30
        key_drivers.append(f"High alcohol intake ({lifestyle.alcohol_drinks_per_week} drinks/wk)")
    elif lifestyle.alcohol_drinks_per_week >= 7:
        multiplier *= 1.15

    # Dietary: Red & Processed Meat
    if lifestyle.red_processed_meat_servings_week >= 5:
        multiplier *= 1.25
        key_drivers.append("Frequent processed/red meat consumption (>5 servings/wk)")

    # Dietary: Fiber deficiency vs sufficiency
    if lifestyle.dietary_fiber_grams_day < 15.0:
        multiplier *= 1.20
        key_drivers.append(f"Low dietary fiber intake ({lifestyle.dietary_fiber_grams_day:.1f}g/day, <15g threshold)")
    elif lifestyle.dietary_fiber_grams_day >= 28.0:
        multiplier *= 0.85

    # Dietary: Ultra-processed food %
    if lifestyle.ultra_processed_food_pct >= 40.0:
        multiplier *= 1.20
        key_drivers.append(f"High ultra-processed food diet ({lifestyle.ultra_processed_food_pct:.0f}% of daily calories)")

    # Mediterranean diet protective factor
    if lifestyle.mediterranean_diet_score >= 8:
        multiplier *= 0.88
    elif lifestyle.mediterranean_diet_score <= 3:
        multiplier *= 1.12

    # Physical activity protective factor
    if lifestyle.physical_activity_hours_week >= 3.0:
        multiplier *= 0.85

    risk_pct = min(50.0, base_rate * multiplier)

    return {
        "risk_pct": round(risk_pct, 2),
        "population_average_pct": round(base_rate * 1.2, 2),
        "key_drivers": key_drivers
    }

def calculate_breast_risk(profile: PatientProfile) -> Dict[str, Any]:
    """Calculates 10-year breast cancer risk based on sex, genetics, age, ancestry, and lifestyle."""
    if profile.biological_sex.lower() == "male":
        return {
            "risk_pct": 0.08,
            "population_average_pct": 0.08,
            "key_drivers": ["Male biological sex (low baseline)"]
        }

    age = profile.age
    genetics = profile.genetics
    lifestyle = profile.lifestyle

    # Female age baseline (10-year NCI Gail rate)
    if age < 40:
        base_rate = 0.6
    elif age < 50:
        base_rate = 1.7
    elif age < 60:
        base_rate = 2.8
    elif age < 70:
        base_rate = 3.9
    else:
        base_rate = 4.2

    multiplier = 1.0
    key_drivers = []

    # BRCA mutation
    if genetics.brca_mutation:
        multiplier *= 4.80
        key_drivers.append("High penetrance: Pathogenic BRCA1/BRCA2 variant")
    elif genetics.ancestry == "ashkenazi_jewish":
        multiplier *= 1.30
        key_drivers.append("Ashkenazi Jewish ancestry (10x elevated population BRCA carrier frequency)")

    family_bc = any("breast" in f.lower() or "ovarian" in f.lower() for f in genetics.family_cancer_history)
    if family_bc:
        multiplier *= 1.90
        key_drivers.append("First-degree relative diagnosed with breast cancer")

    # Alcohol consumption (NCCN/WCRF: >3 drinks/week has measurable hazard ratio)
    if lifestyle.alcohol_drinks_per_week > 7:
        multiplier *= 1.22
        key_drivers.append(f"Alcohol consumption ({lifestyle.alcohol_drinks_per_week} drinks/wk)")

    # Post-menopausal obesity
    if age >= 50 and lifestyle.bmi >= 30:
        multiplier *= 1.25
        key_drivers.append(f"Post-menopausal elevated BMI ({lifestyle.bmi:.1f})")

    # Dietary factors (ultra-processed foods & low Mediterranean diet score)
    if lifestyle.ultra_processed_food_pct >= 40.0:
        multiplier *= 1.12
    if lifestyle.mediterranean_diet_score >= 8:
        multiplier *= 0.90

    risk_pct = min(60.0, base_rate * multiplier)

    return {
        "risk_pct": round(risk_pct, 2),
        "population_average_pct": round(base_rate * 1.1, 2),
        "key_drivers": key_drivers
    }

def calculate_cervical_risk(profile: PatientProfile) -> Dict[str, Any]:
    """Calculates 10-year cervical cancer risk based on HPV vaccination, Pap screening, smoking, and immune factors."""
    if profile.biological_sex.lower() == "male":
        return {
            "risk_pct": 0.01,
            "population_average_pct": 0.01,
            "key_drivers": ["Male biological sex (cervical tissue absent)"]
        }

    age = profile.age
    lifestyle = profile.lifestyle
    screening = profile.screening

    # Female age baseline rate (10-year cumulative SEER rate)
    if age < 25:
        base_rate = 0.25
    elif age < 40:
        base_rate = 0.85
    elif age < 55:
        base_rate = 1.10
    elif age < 70:
        base_rate = 0.70
    else:
        base_rate = 0.40

    multiplier = 1.0
    key_drivers = []

    # HPV Vaccination Status
    if screening.hpv_vaccinated:
        vac_age = screening.hpv_vaccine_age_administered or 16
        if vac_age <= 18:
            multiplier *= 0.15  # 85% risk reduction if completed in adolescence
            key_drivers.append(f"Protective: 9-valent HPV vaccinated at age {vac_age} (85% risk reduction)")
        elif vac_age <= 26:
            multiplier *= 0.25  # 75% risk reduction
            key_drivers.append(f"Protective: HPV vaccinated at age {vac_age}")
        else:
            multiplier *= 0.50
            key_drivers.append("HPV catch-up vaccination received in adulthood")
    else:
        multiplier *= 1.80
        key_drivers.append("Unvaccinated against high-risk oncogenic HPV (HPV 16/18/31/45)")

    # Pap Smear / HPV Co-testing History
    last_pap = screening.last_pap_smear_years_ago
    if last_pap is None or last_pap > 5.0:
        multiplier *= 2.20
        key_drivers.append("Overdue for USPSTF cervical cytology/hrHPV co-testing (>5 years or never)")
    elif last_pap > 3.0 and age < 30:
        multiplier *= 1.40
        key_drivers.append("Overdue for 3-year cervical cytology screening")
    else:
        multiplier *= 0.60
        key_drivers.append(f"Protective: Up-to-date cervical screening (last Pap/HPV {last_pap:.1f} yrs ago)")

    # Cytology History
    if screening.abnormal_pap_history:
        multiplier *= 2.10
        key_drivers.append("Prior history of abnormal cervical cytology (ASCUS / LSIL / HSIL)")

    # Smoking synergistic co-factor (impairs local cervical mucosal immunity)
    if lifestyle.smoking_status == "current":
        multiplier *= 1.70
        key_drivers.append("Current tobacco use (impairs cervical clearance of persistent hrHPV)")

    risk_pct = min(35.0, base_rate * multiplier)

    return {
        "risk_pct": round(risk_pct, 2),
        "population_average_pct": round(base_rate * 1.0, 2),
        "key_drivers": key_drivers
    }

def calculate_prostate_risk(profile: PatientProfile) -> Dict[str, Any]:
    """Calculates 10-year prostate cancer risk based on age, ancestry, family history, BRCA variants, and PSA."""
    if profile.biological_sex.lower() == "female":
        return {
            "risk_pct": 0.01,
            "population_average_pct": 0.01,
            "key_drivers": ["Female biological sex (prostate tissue absent)"]
        }

    age = profile.age
    genetics = profile.genetics
    lifestyle = profile.lifestyle
    screening = profile.screening

    # Male age baseline rate (10-year cumulative SEER rate)
    if age < 45:
        base_rate = 0.20
    elif age < 55:
        base_rate = 1.80
    elif age < 65:
        base_rate = 5.20
    elif age < 75:
        base_rate = 8.50
    else:
        base_rate = 9.80

    multiplier = 1.0
    key_drivers = []

    # African ancestry multiplier (SEER / USPSTF: 1.7x incidence and higher mortality)
    if genetics.ancestry == "african":
        multiplier *= 1.75
        key_drivers.append("African genetic ancestry (1.75x hazard ratio per USPSTF Grade C evidence)")

    # Family history of prostate cancer
    family_prostate = any("prostate" in f.lower() for f in genetics.family_cancer_history)
    if family_prostate:
        multiplier *= 2.10
        key_drivers.append("First-degree relative diagnosed with prostate cancer (2.1x familial multiplier)")

    # BRCA2 / ATM germline mutations (aggressive phenotype)
    if genetics.brca_mutation:
        multiplier *= 3.40
        key_drivers.append("Germline BRCA1/2 mutation (3.4x hazard of early-onset, high-grade Gleason disease)")

    # Baseline Serum PSA level if known
    if screening.baseline_psa_ng_ml is not None:
        psa = screening.baseline_psa_ng_ml
        if psa > 10.0:
            multiplier *= 3.80
            key_drivers.append(f"Markedly elevated serum PSA ({psa:.1f} ng/mL > 10.0 threshold)")
        elif psa >= 4.0:
            multiplier *= 2.20
            key_drivers.append(f"Elevated baseline PSA ({psa:.1f} ng/mL > 4.0 clinical threshold)")
        elif psa < 1.0 and age >= 50:
            multiplier *= 0.65
            key_drivers.append(f"Reassuring baseline PSA ({psa:.1f} ng/mL < 1.0)")

    # Diet and metabolic factors
    if lifestyle.bmi >= 30:
        multiplier *= 1.20
        key_drivers.append("Obesity (correlated with higher risk of aggressive Gleason 8-10 disease)")
    if lifestyle.red_processed_meat_servings_week >= 5:
        multiplier *= 1.15

    risk_pct = min(60.0, base_rate * multiplier)

    return {
        "risk_pct": round(risk_pct, 2),
        "population_average_pct": round(base_rate * 1.1, 2),
        "key_drivers": key_drivers
    }

def calculate_health_score(profile: PatientProfile) -> float:
    """Computes an overall systemic baseline health score (0-100) deterministically from multi-organ factors."""
    score = 100.0

    # Smoking deductions
    if profile.lifestyle.smoking_status == "current":
        score -= min(35.0, profile.lifestyle.pack_years * 0.8 + 15.0)
    elif profile.lifestyle.smoking_status == "former":
        quit_bonus = min(10.0, (profile.lifestyle.years_since_quitting or 0) * 1.2)
        score -= max(2.0, profile.lifestyle.pack_years * 0.4 - quit_bonus)

    # BMI deductions
    bmi = profile.lifestyle.bmi
    if bmi > 25.0:
        score -= min(15.0, (bmi - 25.0) * 1.5)
    elif bmi < 18.5:
        score -= 5.0

    # Alcohol deductions
    if profile.lifestyle.alcohol_drinks_per_week > 7.0:
        score -= min(12.0, (profile.lifestyle.alcohol_drinks_per_week - 7.0) * 0.9)

    # Physical activity bonus/deduction
    if profile.lifestyle.physical_activity_hours_week >= 3.0:
        score += 3.0
    elif profile.lifestyle.physical_activity_hours_week < 1.0:
        score -= 6.0

    # Diet quality (Fiber, UPF %, Med diet)
    if profile.lifestyle.dietary_fiber_grams_day < 15.0:
        score -= 4.0
    elif profile.lifestyle.dietary_fiber_grams_day >= 28.0:
        score += 2.0

    if profile.lifestyle.ultra_processed_food_pct > 35.0:
        score -= min(6.0, (profile.lifestyle.ultra_processed_food_pct - 35.0) * 0.15)

    if profile.lifestyle.mediterranean_diet_score >= 8:
        score += 3.0
    elif profile.lifestyle.mediterranean_diet_score <= 3:
        score -= 4.0

    # Environmental deductions
    if profile.environmental.pm25_exposure_ug_m3 > 35.0:
        score -= min(7.0, (profile.environmental.pm25_exposure_ug_m3 - 35.0) * 0.15)
    if profile.environmental.residential_radon_risk == "high":
        score -= 5.0

    # Screening diligence bonus / penalty
    if profile.screening.hpv_vaccinated:
        score += 2.0
    if profile.genetics.brca_mutation:
        score -= 8.0
    if profile.genetics.lynch_syndrome:
        score -= 8.0

    return round(max(15.0, min(99.0, score)), 1)

def generate_risk_trajectory(
    baseline_10yr: float,
    counterfactual_10yr: float,
    years: int = 10
) -> List[RiskTrajectoryPoint]:
    """Generates an annualized cumulative risk trajectory curve from Year 1 to Year N (supports up to 30 years)."""
    points = []
    for y in range(1, years + 1):
        t_factor = y / years
        
        # Interventions accumulate physiological benefit over time
        sim_progress = 1.0 - math.exp(-0.35 * y)
        effective_counterfactual = baseline_10yr - (baseline_10yr - counterfactual_10yr) * sim_progress
        
        base_y = round(baseline_10yr * (t_factor ** 1.08), 2)
        sim_y = round(max(0.02, effective_counterfactual * (t_factor ** 1.08)), 2)
        
        points.append(RiskTrajectoryPoint(
            year=y,
            baseline_risk_pct=base_y,
            counterfactual_risk_pct=sim_y
        ))
    return points
