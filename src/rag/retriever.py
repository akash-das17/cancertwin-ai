from typing import List, Optional
from src.rag.vector_store import ChromaManager
from src.models.risk_report import GuidelineEvidence
from src.tools.pubmed_tool import PubMedTool

CONFIDENCE_DISTANCE_THRESHOLD = 1.15

class OncologyRetriever:
    """Retrieves clinical oncology guidelines from ChromaDB, with automatic PubMed live search on low confidence."""
    
    def __init__(self, vector_store: Optional[ChromaManager] = None, pubmed_tool: Optional[PubMedTool] = None):
        self.vector_store = vector_store or ChromaManager()
        self.pubmed_tool = pubmed_tool or PubMedTool()

    def retrieve_guidelines(
        self,
        query: str,
        cancer_type: Optional[str] = None,
        top_k: int = 2
    ) -> List[GuidelineEvidence]:
        """Searches ChromaDB for relevant evidence; triggers live PubMed query if distance is above threshold."""
        hits = self.vector_store.query(query_text=query, n_results=top_k, cancer_type=cancer_type)
        evidence_list = []
        low_confidence = False

        if not hits:
            low_confidence = True
        else:
            top_dist = hits[0].get("distance", 0.0)
            if top_dist > CONFIDENCE_DISTANCE_THRESHOLD:
                low_confidence = True

        for hit in hits:
            meta = hit.get("metadata", {})
            evidence_list.append(GuidelineEvidence(
                id=hit.get("id", "UNK"),
                cancer_type=meta.get("cancer_type", cancer_type or "General"),
                title=meta.get("title", "Clinical Recommendation"),
                source=meta.get("source", "Medical Guideline"),
                excerpt=meta.get("summary", hit.get("document", "")[:300]),
                hazard_ratio=meta.get("hazard_ratio", None),
                evidence_level=meta.get("evidence_level", None),
                url=meta.get("url") or meta.get("source_url") or f"https://pubmed.ncbi.nlm.nih.gov/?term={meta.get('title', 'oncology+guidelines').replace(' ', '+')}"
            ))

        # Dynamic Threshold Escaping: If confidence is low or specific mutation is missing, query live PubMed
        if low_confidence:
            print(f"[OncologyRetriever] ChromaDB low confidence for query '{query}'. Triggering PubMed live search...")
            try:
                pubmed_articles = self.pubmed_tool.search_pubmed(query, max_results=2)
                for art in pubmed_articles:
                    evidence_list.append(GuidelineEvidence(
                        id=art["id"],
                        cancer_type=cancer_type or "Research Literature",
                        title=art["title"],
                        source=f"PubMed / {art['source']}",
                        excerpt=art["summary"],
                        hazard_ratio=None,
                        evidence_level="PubMed Live Research",
                        url=art["url"]
                    ))
            except Exception as e:
                print(f"[OncologyRetriever] PubMed fallback error: {e}")

        return evidence_list

    def retrieve_live_pubmed(
        self,
        query: str,
        cancer_type: Optional[str] = None,
        max_results: int = 2
    ) -> List[GuidelineEvidence]:
        """Directly retrieves real-time clinical trials and literature from NCBI PubMed."""
        evidence_list = []
        try:
            pubmed_articles = self.pubmed_tool.search_pubmed(query, max_results=max_results)
            for art in pubmed_articles:
                evidence_list.append(GuidelineEvidence(
                    id=art["id"],
                    cancer_type=cancer_type or "Research Literature",
                    title=art["title"],
                    source=f"PubMed / {art['source']}",
                    excerpt=art["summary"],
                    hazard_ratio=None,
                    evidence_level="PubMed Live Research",
                    url=art["url"]
                ))
        except Exception as e:
            print(f"[OncologyRetriever] Live PubMed retrieval error: {e}")
        return evidence_list

    def get_risk_context_for_cancer(self, cancer_type: str, patient_summary: str) -> List[GuidelineEvidence]:
        """Specialized retrieval query for baseline cancer risk assessment."""
        query = f"Risk factors, hazard ratios, and screening criteria for {cancer_type} cancer: {patient_summary}"
        return self.retrieve_guidelines(query=query, cancer_type=cancer_type, top_k=2)

    def get_intervention_evidence(self, cancer_type: str, intervention_name: str) -> List[GuidelineEvidence]:
        """Specialized retrieval query for counterfactual interventions."""
        query = f"Impact of {intervention_name} on {cancer_type} cancer relative risk reduction and mortality"
        return self.retrieve_guidelines(query=query, cancer_type=cancer_type, top_k=2)
