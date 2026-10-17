import os
import re
from typing import List, Dict, Any
from backend.app.database.vector_store import vector_store

def ingest_reports(reports_dir: str = None) -> int:
    if reports_dir is None:
        reports_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..", "data", "reports"))
    
    if not os.path.exists(reports_dir):
        raise FileNotFoundError(f"Reports directory not found: {reports_dir}")
        
    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    
    report_files = [f for f in os.listdir(reports_dir) if f.endswith(".md")]
    
    for filename in report_files:
        filepath = os.path.join(reports_dir, filename)
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
            
        # Extract report headers
        rep_id_match = re.search(r"\*\*Report ID:\*\*\s*(R-\d+)", content)
        rep_id = rep_id_match.group(1) if rep_id_match else filename.split("_")[0]
        
        sector_match = re.search(r"\*\*Sector:\*\*\s*(.+)", content)
        sector = sector_match.group(1).strip() if sector_match else "General"
        
        access_match = re.search(r"\*\*Access:\*\*\s*(.+)", content)
        access = access_match.group(1).strip().lower() if access_match else "paid"
        
        # Split by page marker
        pages = re.split(r"<!--\s*Page\s*(\d+)\s*-->", content)
        
        if len(pages) > 1:
            # pages[0] is header, followed by pairs (page_num, page_content)
            for i in range(1, len(pages), 2):
                page_num = int(pages[i])
                page_body = pages[i+1].strip()
                if not page_body:
                    continue
                
                # Tag region and year heuristically
                region = "APAC" if "Asia-Pacific" in page_body or "APAC" in page_body else "Global"
                year = "2024" if "2024" in page_body else "2025"
                
                chunk_id = f"{rep_id}_p{page_num}"
                ids.append(chunk_id)
                documents.append(page_body)
                metadatas.append({
                    "report_id": rep_id,
                    "sector": sector,
                    "access": access,
                    "page": page_num,
                    "region": region,
                    "year": year
                })
        else:
            # Single page document fallback
            ids.append(f"{rep_id}_p1")
            documents.append(content.strip())
            metadatas.append({
                "report_id": rep_id,
                "sector": sector,
                "access": access,
                "page": 1,
                "region": "Global",
                "year": "2025"
            })
            
    vector_store.add_chunks(ids=ids, documents=documents, metadatas=metadatas)
    return len(ids)

if __name__ == "__main__":
    count = ingest_reports()
    print(f"Successfully ingested {count} chunks into ChromaDB.")
