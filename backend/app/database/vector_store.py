import os
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings as ChromaSettings

class VectorStoreManager:
    def __init__(self):
        self.persist_directory = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "chroma_data"))
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="market_reports",
            metadata={"hnsw:space": "cosine"}
        )

    def add_chunks(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        if not ids:
            return
        self.collection.upsert(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )

    def query_entitled(self, query_text: str, allowed_reports: List[str], n_results: int = 4) -> List[Dict[str, Any]]:
        if not allowed_reports:
            return []
        
        where_filter = None
        if len(allowed_reports) == 1:
            where_filter = {"report_id": allowed_reports[0]}
        else:
            where_filter = {"report_id": {"$in": allowed_reports}}
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where_filter
        )
        
        chunks = []
        if results and "documents" in results and results["documents"]:
            docs = results["documents"][0]
            metas = results["metadatas"][0] if "metadatas" in results else [{}] * len(docs)
            dists = results["distances"][0] if "distances" in results else [0.0] * len(docs)
            for doc, meta, dist in zip(docs, metas, dists):
                chunks.append({
                    "text": doc,
                    "metadata": meta,
                    "score": round(1.0 - float(dist), 4) if dist is not None else 1.0
                })
        return chunks

    def check_unentitled_matches(self, query_text: str, allowed_reports: List[str], n_results: int = 3) -> List[Dict[str, Any]]:
        # Query all documents to detect if relevant info exists in unpurchased reports
        results = self.collection.query(
            query_texts=[query_text],
            n_results=n_results
        )
        unentitled = []
        if results and "metadatas" in results and results["metadatas"]:
            for meta in results["metadatas"][0]:
                rep_id = meta.get("report_id")
                if rep_id and rep_id not in allowed_reports:
                    if meta not in unentitled:
                        unentitled.append(meta)
        return unentitled

    def count(self) -> int:
        return self.collection.count()

vector_store = VectorStoreManager()
