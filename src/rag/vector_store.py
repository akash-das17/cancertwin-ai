import os
import json
from typing import List, Dict, Any, Optional
from pathlib import Path
from src.config import settings

try:
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    CHROMA_AVAILABLE = True
except ImportError:
    chromadb = None
    CHROMA_AVAILABLE = False


class ChromaManager:
    """Manages persistent ChromaDB vector store for oncology clinical guidelines."""
    
    def __init__(self, persist_dir: Optional[str] = None, collection_name: Optional[str] = None):
        self.persist_dir = persist_dir or settings.chroma_persist_dir
        self.collection_name = collection_name or settings.chroma_collection_name
        self._client = None
        self._collection = None
        self._fallback_docs: List[Dict[str, Any]] = []
        
        Path(self.persist_dir).mkdir(parents=True, exist_ok=True)
        self._initialize_store()

    def _initialize_store(self):
        if CHROMA_AVAILABLE and chromadb is not None:
            try:
                self._client = chromadb.PersistentClient(path=self.persist_dir)
                self._collection = self._client.get_or_create_collection(
                    name=self.collection_name,
                    metadata={"description": "Clinical Oncology Guidelines & Risk Factor Evidence"}
                )
            except Exception as e:
                print(f"[ChromaManager] Warning initializing ChromaDB: {e}. Using resilient memory store.")
                self._fallback_init()
        else:
            self._fallback_init()

    def _fallback_init(self):
        # Resilient in-memory fallback if chromadb is not yet installed in active environment
        fallback_file = Path(self.persist_dir) / "fallback_store.json"
        if fallback_file.exists():
            try:
                with open(fallback_file, "r", encoding="utf-8") as f:
                    self._fallback_docs = json.load(f)
            except Exception:
                self._fallback_docs = []

    def add_guidelines(
        self,
        ids: List[str],
        documents: List[str],
        metadatas: List[Dict[str, Any]]
    ):
        """Add clinical guidelines with metadata to the vector database."""
        if CHROMA_AVAILABLE and self._collection is not None:
            try:
                self._collection.upsert(
                    ids=ids,
                    documents=documents,
                    metadatas=metadatas  # type: ignore[arg-type]
                )
            except Exception as e:
                print(f"[ChromaManager] Upsert error: {e}")

        # Always keep fallback store synchronized
        for doc_id, doc, meta in zip(ids, documents, metadatas):
            existing = [d for d in self._fallback_docs if d["id"] == doc_id]
            entry = {"id": doc_id, "document": doc, "metadata": meta}
            if existing:
                self._fallback_docs[self._fallback_docs.index(existing[0])] = entry
            else:
                self._fallback_docs.append(entry)
        
        fallback_file = Path(self.persist_dir) / "fallback_store.json"
        try:
            with open(fallback_file, "w", encoding="utf-8") as f:
                json.dump(self._fallback_docs, f, indent=2)
        except Exception as e:
            print(f"[ChromaManager] Error saving fallback store: {e}")

    def query(
        self,
        query_text: str,
        n_results: int = 3,
        cancer_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Query relevant guidelines with optional cancer type filtering."""
        results_formatted = []
        
        if CHROMA_AVAILABLE and self._collection is not None:
            where_filter = {"cancer_type": cancer_type} if cancer_type else None
            try:
                query_kwargs: Dict[str, Any] = {
                    "query_texts": [query_text],
                    "n_results": n_results
                }
                if where_filter:
                    query_kwargs["where"] = where_filter
                    
                raw = self._collection.query(**query_kwargs)
                
                if raw and raw.get("ids") and len(raw["ids"][0]) > 0:
                    raw_docs = raw.get("documents") or []
                    raw_metas = raw.get("metadatas") or []
                    raw_dists = raw.get("distances") or []
                    for i in range(len(raw["ids"][0])):
                        results_formatted.append({
                            "id": raw["ids"][0][i],
                            "document": raw_docs[0][i] if (len(raw_docs) > 0 and raw_docs[0] is not None) else "",
                            "metadata": raw_metas[0][i] if (len(raw_metas) > 0 and raw_metas[0] is not None) else {},
                            "distance": raw_dists[0][i] if (len(raw_dists) > 0 and raw_dists[0] is not None) else 0.0
                        })
                return results_formatted
            except Exception as e:
                print(f"[ChromaManager] Query error, falling back to local search: {e}")

        # Fallback keyword and semantic scoring
        query_terms = set(query_text.lower().split())
        matched = []
        for item in self._fallback_docs:
            if cancer_type and item.get("metadata", {}).get("cancer_type", "").lower() != cancer_type.lower():
                continue
            doc_text = (item.get("document", "") + " " + item.get("metadata", {}).get("title", "")).lower()
            overlap = sum(1 for term in query_terms if term in doc_text)
            matched.append((overlap, item))
            
        matched.sort(key=lambda x: x[0], reverse=True)
        for _, item in matched[:n_results]:
            results_formatted.append({
                "id": item["id"],
                "document": item["document"],
                "metadata": item["metadata"],
                "distance": 0.2
            })
            
        return results_formatted

    def count(self) -> int:
        """Returns total number of guidelines stored in ChromaDB or fallback store."""
        if CHROMA_AVAILABLE and self._collection is not None:
            try:
                return self._collection.count()
            except Exception:
                pass
        return len(self._fallback_docs)
