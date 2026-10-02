"""
PubMed / NCBI E-Utilities & Genomic Variant Query Tool for CancerTwin AI.
Queries live medical literature from PubMed when local knowledge base confidence is low,
or when unknown / rare genomic mutations are evaluated.
"""
import requests
import json
import urllib.parse
from typing import List, Dict, Any, Optional

NCBI_ESEARCH_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
NCBI_ESUMMARY_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"

# Pre-indexed clinical evidence cache for common high-impact rare oncogenic variants
KNOWN_VARIANT_CATALOG: Dict[str, Dict[str, Any]] = {
    "BRAF_V600E": {
        "gene": "BRAF",
        "alteration": "V600E",
        "cancer_types": ["Melanoma", "Colorectal", "Non-Small Cell Lung", "Thyroid"],
        "actionability": "FDA-Approved Targeted Therapies (Tier 1A)",
        "therapies": "Dabrafenib + Trametinib (BRAF/MEK inhibition), Encorafenib + Cetuximab (in CRC)",
        "clinical_significance": "Constitutively activates MAPK/ERK signaling; high risk of aggressive disease, but responds to dual BRAF/MEK blockade.",
        "pmid": "31566309",
        "url": "https://pubmed.ncbi.nlm.nih.gov/31566309/",
        "key_trial": "BEACON CRC (N Engl J Med 2019) / COMBI-d (Lancet)"
    },
    "KRAS_G12C": {
        "gene": "KRAS",
        "alteration": "G12C",
        "cancer_types": ["Non-Small Cell Lung", "Colorectal"],
        "actionability": "FDA-Approved Covalent Inhibitors (Tier 1A)",
        "therapies": "Sotorasib (Lumakras), Adagrasib (Krazati)",
        "clinical_significance": "Locks KRAS in active GTP-bound oncogenic state; direct covalent inhibitors trap mutant protein in inactive GDP conformation.",
        "pmid": "36881944",
        "url": "https://pubmed.ncbi.nlm.nih.gov/36881944/",
        "key_trial": "CodeBreaK 200 (Lancet 2023) / KRYSTAL-1 (N Engl J Med)"
    },
    "NTRK_FUSION": {
        "gene": "NTRK1/2/3",
        "alteration": "Gene Fusion (ETV6-NTRK3, TPM3-NTRK1)",
        "cancer_types": ["Tumor-Agnostic", "Secretory Breast", "Colorectal", "Glioblastoma"],
        "actionability": "Tumor-Agnostic Precision Oncology (Tier 1A)",
        "therapies": "Larotrectinib (Vitrakvi), Entrectinib (Rozlytrek)",
        "clinical_significance": "Constitutive TRK kinase domain activation; achieves >75% objective response rates regardless of anatomical tumor histology.",
        "pmid": "29466156",
        "url": "https://pubmed.ncbi.nlm.nih.gov/29466156/",
        "key_trial": "NAVIGATE / STARTRK-2 (N Engl J Med 2018)"
    },
    "RET_FUSION": {
        "gene": "RET",
        "alteration": "Fusion (KIF5B-RET, CCDC6-RET)",
        "cancer_types": ["Non-Small Cell Lung", "Medullary Thyroid"],
        "actionability": "FDA-Approved Selective RET Inhibitors (Tier 1A)",
        "therapies": "Selpercatinib (Retevmo), Pralsetinib (Gavreto)",
        "clinical_significance": "Receptor tyrosine kinase fusion with robust intracranial penetration and durable disease control in EGFR/ALK-negative NSCLC.",
        "pmid": "32849378",
        "url": "https://pubmed.ncbi.nlm.nih.gov/32849378/",
        "key_trial": "LIBRETTO-001 (N Engl J Med 2020)"
    },
    "HER2_EXON20": {
        "gene": "ERBB2 (HER2)",
        "alteration": "Exon 20 In-Frame Insertion (A775_G776insYVMA)",
        "cancer_types": ["Non-Small Cell Lung", "Breast"],
        "actionability": "Antibody-Drug Conjugate / Targeted TKI (Tier 1B)",
        "therapies": "Trastuzumab Deruxtecan (Enhertu), Mobocertinib",
        "clinical_significance": "Stereochemical resistance to first-generation EGFR/HER2 TKIs; highly sensitive to antibody-drug conjugate endocytosis.",
        "pmid": "34534430",
        "url": "https://pubmed.ncbi.nlm.nih.gov/34534430/",
        "key_trial": "DESTINY-Lung01 (N Engl J Med 2022)"
    }
}

class PubMedTool:
    """Tool that performs real-time queries to NCBI PubMed E-Utilities and genomic databases."""

    def __init__(self, timeout_sec: float = 4.0):
        self.timeout = timeout_sec

    def _clean_search_term(self, query: str) -> str:
        """Sanitizes conversational queries into concise clinical PubMed search terms."""
        if not query:
            return ""
        
        lower_q = query.lower()
        # 1. If explicit alteration / mutation marker is present
        for marker in ["alteration:", "alterations:", "mutation:", "mutations:", "variant:", "genomics:"]:
            if marker in lower_q:
                idx = lower_q.find(marker)
                alteration_match = query[idx + len(marker):].split(",")[0].split(".")[0].strip()
                cancer_words = ["lung", "colorectal", "breast", "cervical", "prostate", "melanoma", "colon", "ovarian"]
                found_cancers = [c for c in cancer_words if c in lower_q]
                cancer_str = found_cancers[0].title() if found_cancers else ""
                return f"{cancer_str} {alteration_match} targeted therapy clinical trial".strip()

        # 2. Check for known oncogenes / variants in text
        gene_keywords = ["ntrk", "braf", "kras", "ret", "her2", "erbb2", "egfr", "alk", "ros1", "met", "ctdna"]
        found_genes = [g for g in gene_keywords if g in lower_q]
        if found_genes:
            cancer_words = ["lung", "colorectal", "breast", "cervical", "prostate", "melanoma", "colon"]
            found_cancers = [c for c in cancer_words if c in lower_q]
            cancer_str = found_cancers[0].title() if found_cancers else ""
            return f"{cancer_str} {' '.join(found_genes)} targeted therapy".strip()

        # 3. If query has more than 6 words, extract key medical nouns
        words = query.replace(":", " ").replace(",", " ").replace(";", " ").split()
        if len(words) > 6:
            stopwords = {"risk", "factors", "hazard", "ratios", "and", "screening", "criteria", "for", "patient", "summary", "age", "male", "female", "smoking", "never", "former", "current", "pack-yrs", "bmi", "ancestry", "general", "ug/m3"}
            filtered = [w for w in words if w.lower() not in stopwords]
            return " ".join(filtered[:5])

        return query

    def search_pubmed(self, query: str, max_results: int = 3) -> List[Dict[str, Any]]:
        """
        Executes a real-time literature search via NCBI Entrez E-Utilities.
        Returns a list of articles with Title, Source, Year, PMID, and direct PubMed URL.
        """
        results = []
        term_to_search = self._clean_search_term(query) or query
        try:
            # 1. Search for PMIDs
            params = {
                "db": "pubmed",
                "term": term_to_search,
                "retmode": "json",
                "retmax": max_results,
                "sort": "pub_date"
            }
            resp = requests.get(NCBI_ESEARCH_URL, params=params, timeout=self.timeout)
            if resp.status_code != 200:
                return results

            id_list = resp.json().get("esearchresult", {}).get("idlist", [])
            if not id_list and term_to_search != query:
                # Retry with original query if clean term didn't match
                params["term"] = query
                resp = requests.get(NCBI_ESEARCH_URL, params=params, timeout=self.timeout)
                if resp.status_code == 200:
                    id_list = resp.json().get("esearchresult", {}).get("idlist", [])

            if not id_list:
                return results

            # 2. Fetch document summaries
            summary_params = {
                "db": "pubmed",
                "id": ",".join(id_list),
                "retmode": "json"
            }
            sum_resp = requests.get(NCBI_ESUMMARY_URL, params=summary_params, timeout=self.timeout)
            if sum_resp.status_code != 200:
                return results

            result_data = sum_resp.json().get("result", {})
            for pmid in id_list:
                doc = result_data.get(pmid)
                if not doc:
                    continue
                title = doc.get("title", "Clinical Research Article").rstrip(".")
                source = doc.get("source", "PubMed Central")
                pubdate = doc.get("pubdate", "")
                authors = doc.get("authors", [])
                first_author = authors[0].get("name", "Medical Team") if authors else "Author Team"
                
                results.append({
                    "id": f"PUBMED-{pmid}",
                    "pmid": pmid,
                    "title": title,
                    "source": f"{source} ({pubdate})",
                    "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    "first_author": first_author,
                    "summary": f"Recent clinical literature retrieved via live PubMed query for '{query}'. Author: {first_author} et al."
                })

        except Exception as e:
            print(f"[PubMedTool] Live search exception: {e}")

        return results

    def lookup_variant_knowledge(self, gene: str, mutation: Optional[str] = None) -> Dict[str, Any]:
        """
        Looks up clinical actionability, targeted therapies, and trials for specific genomic mutations.
        Checks known catalog first, then falls back to a live PubMed query.
        """
        clean_gene = gene.strip().upper()
        clean_mut = (mutation or "").strip().upper()
        key = f"{clean_gene}_{clean_mut}"

        # 1. Check known variant catalog
        for cat_key, entry in KNOWN_VARIANT_CATALOG.items():
            if cat_key == key or clean_gene == entry["gene"] and (not clean_mut or clean_mut in entry["alteration"]):
                return {
                    "found": True,
                    "source": "Clinical Precision Oncology Catalog",
                    "data": entry
                }

        # 2. Live PubMed fallback search for obscure / rare mutations
        pubmed_query = f"{clean_gene} {clean_mut} targeted therapy clinical trial oncology"
        articles = self.search_pubmed(pubmed_query, max_results=2)
        if articles:
            return {
                "found": True,
                "source": "PubMed Live Query",
                "data": {
                    "gene": clean_gene,
                    "alteration": clean_mut or "Novel alteration",
                    "cancer_types": ["Precision Oncology"],
                    "actionability": "Under Clinical Trial Investigation",
                    "therapies": "Clinical trial enrollment or basket trial matched to genomic alterations.",
                    "clinical_significance": f"Retrieved {len(articles)} recent medical publications investigating {clean_gene} {clean_mut}.",
                    "pmid": articles[0]["pmid"],
                    "url": articles[0]["url"],
                    "key_trial": articles[0]["title"]
                }
            }

        return {
            "found": False,
            "gene": clean_gene,
            "alteration": clean_mut,
            "message": f"No definitive FDA-approved targeted therapy identified for {clean_gene} {clean_mut}."
        }
