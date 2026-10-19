import os
from typing import List, Dict, Any, Optional
import chromadb
from backend.app.config import settings

class VectorStoreManager:
    def __init__(self):
        self.persist_directory = os.path.abspath(settings.VECTOR_STORE_DIR)
        os.makedirs(self.persist_directory, exist_ok=True)
        self.client = chromadb.PersistentClient(path=self.persist_directory)
        self.collection = self.client.get_or_create_collection(
            name="market_reports",
            metadata={"hnsw:space": "cosine"}
        )
        self._ready = False
        self._indexed_report_ids_cache = None

    def set_ready(self, ready: bool) -> None:
        self._ready = bool(ready)

    def is_ready(self) -> bool:
        return self._ready

    def add_chunks(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        if not ids:
            return
        batch_size = 3000
        for offset in range(0, len(ids), batch_size):
            end = offset + batch_size
            self.collection.upsert(
                ids=ids[offset:end],
                documents=documents[offset:end],
                metadatas=metadatas[offset:end],
            )
        self._indexed_report_ids_cache = None

    def replace_all_chunks(self, ids: List[str], documents: List[str], metadatas: List[Dict[str, Any]]):
        """Upsert the full new corpus before deleting stale IDs."""
        existing = self.collection.get(include=["metadatas"]).get("ids", [])
        self.add_chunks(ids, documents, metadatas)
        new_ids = set(ids)
        stale_ids = [chunk_id for chunk_id in existing if chunk_id not in new_ids]
        if stale_ids:
            self.collection.delete(ids=stale_ids)
        self._indexed_report_ids_cache = None

    def query_entitled(self, query_text: str, allowed_reports: List[str], n_results: int = 4) -> List[Dict[str, Any]]:
        collection_count = self.collection.count()
        if not allowed_reports or collection_count == 0:
            return []
        
        where_filter = None
        if len(allowed_reports) == 1:
            where_filter = {"report_id": allowed_reports[0]}
        else:
            where_filter = {"report_id": {"$in": allowed_reports}}
            
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection_count),
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
        collection_count = self.collection.count()
        if collection_count == 0:
            return []
        results = self.collection.query(
            query_texts=[query_text],
            n_results=min(n_results, collection_count)
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

    def indexed_report_ids(self) -> List[str]:
        if self._indexed_report_ids_cache is None:
            report_ids = set()
            offset = 0
            page_size = 5000
            while True:
                metadata_page = self.collection.get(include=["metadatas"], limit=page_size, offset=offset).get("metadatas", [])
                report_ids.update(
                    str(metadata["report_id"])
                    for metadata in metadata_page
                    if isinstance(metadata, dict) and metadata.get("report_id")
                )
                if len(metadata_page) < page_size:
                    break
                offset += page_size
            self._indexed_report_ids_cache = sorted(report_ids)
        return list(self._indexed_report_ids_cache)

vector_store = VectorStoreManager()
