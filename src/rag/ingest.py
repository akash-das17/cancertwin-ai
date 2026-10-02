import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.config import settings, RAW_GUIDELINES_DIR
from src.rag.vector_store import ChromaManager

def load_guideline_files(guidelines_dir: Path) -> List[Dict[str, Any]]:
    """Loads all json files from the raw_guidelines directory."""
    all_guidelines = []
    if not guidelines_dir.exists():
        print(f"[Ingest] Directory not found: {guidelines_dir}")
        return all_guidelines
        
    for json_file in guidelines_dir.glob("*.json"):
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    all_guidelines.extend(data)
                elif isinstance(data, dict):
                    all_guidelines.append(data)
            print(f"[Ingest] Loaded guidelines from {json_file.name}")
        except Exception as e:
            print(f"[Ingest] Failed loading {json_file}: {e}")
            
    return all_guidelines

def ingest_all_guidelines(persist_dir: Optional[str] = None) -> int:
    """Ingests raw guideline JSONs into ChromaDB."""
    manager = ChromaManager(persist_dir=persist_dir)
    guidelines = load_guideline_files(RAW_GUIDELINES_DIR)
    
    if not guidelines:
        print("[Ingest] No guideline records found to ingest.")
        return 0
        
    ids = []
    documents = []
    metadatas = []
    
    for g in guidelines:
        g_id = g.get("id", f"GUIDE-{len(ids)}")
        cancer_type = g.get("cancer_type", "General")
        title = g.get("title", "Clinical Oncology Guideline")
        source = g.get("source", "Standard Practice")
        summary = g.get("summary", "")
        hazard_ratio = float(g.get("hazard_ratio", 1.0))
        evidence_level = g.get("evidence_level", "Standard")
        url = g.get("url") or g.get("source_url") or ""
        
        # Build comprehensive document text for vector embedding
        doc_text = f"Title: {title}\nCancer Type: {cancer_type}\nSource: {source}\nSummary: {summary}\n"
        if url:
            doc_text += f"Reference Link: {url}\n"
        if "interventions" in g:
            for k, v in g["interventions"].items():
                if isinstance(v, dict):
                    desc = v.get("description", "")
                    doc_text += f"\nIntervention ({k}): {desc}"
        if "risk_factors" in g:
            doc_text += f"\nRisk Factors: {', '.join(g['risk_factors'])}"
            
        ids.append(g_id)
        documents.append(doc_text)
        metadatas.append({
            "cancer_type": cancer_type,
            "title": title,
            "source": source,
            "hazard_ratio": hazard_ratio,
            "evidence_level": evidence_level,
            "summary": summary,
            "url": url
        })
        
    manager.add_guidelines(ids=ids, documents=documents, metadatas=metadatas)
    print(f"[Ingest] Successfully ingested {len(ids)} oncology guidelines into ChromaDB.")
    return len(ids)

if __name__ == "__main__":
    ingest_all_guidelines()
