"""Validate and index authorized Markdown/PDF report files."""
import json
import logging
import os
import re
import threading
from datetime import datetime
from typing import Any, Dict, List, Tuple

from pypdf import PdfReader

from backend.app.config import settings
from backend.app.database.db import db_manager
from backend.app.database.vector_store import vector_store
from backend.app.guardrails.injection_detector import injection_detector

logger = logging.getLogger(__name__)
_INGEST_LOCK = threading.Lock()


class IngestionBusy(RuntimeError):
    pass
MAX_REPORT_FILES = 200
MAX_FILE_BYTES = 100 * 1024 * 1024
MAX_TOTAL_FILE_BYTES = 500 * 1024 * 1024
MAX_PDF_PAGES = 1500
MAX_PAGE_CHARS = 100_000
MAX_CHUNKS = 100_000
CHUNK_CHARS = 6000
CHUNK_OVERLAP = 300


def _split_page(text: str) -> List[str]:
    """Bound each embedding/model context item while retaining page citations."""
    chunks = []
    start = 0
    while start < len(text):
        hard_end = min(start + CHUNK_CHARS, len(text))
        end = hard_end
        if hard_end < len(text):
            preferred = max(text.rfind("\n", start + CHUNK_CHARS // 2, hard_end),
                            text.rfind(". ", start + CHUNK_CHARS // 2, hard_end))
            if preferred > start:
                end = preferred + (1 if text[preferred] == "\n" else 2)
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= len(text):
            break
        start = max(start + 1, end - CHUNK_OVERLAP)
    return chunks


def _validate_metadata(report: Dict[str, Any], filename: str) -> Dict[str, Any]:
    if not isinstance(report, dict):
        raise ValueError(f"Metadata for {filename} must be a JSON object.")
    values = {key: str(report.get(key, "")).strip() for key in
              ("report_id", "title", "publisher", "published", "sector", "access")}
    if not re.fullmatch(r"R-\d{1,18}", values["report_id"]):
        raise ValueError(f"Report {filename} needs a valid report_id such as R-201.")
    if not values["title"] or len(values["title"]) > 255:
        raise ValueError(f"Report {filename} needs a title of 1 to 255 characters.")
    if not values["publisher"] or len(values["publisher"]) > 100:
        raise ValueError(f"Report {filename} needs a publisher of 1 to 100 characters.")
    if not values["sector"] or len(values["sector"]) > 100:
        raise ValueError(f"Report {filename} needs a sector of 1 to 100 characters.")
    try:
        datetime.strptime(values["published"], "%Y-%m-%d")
    except ValueError as exc:
        raise ValueError(f"Report {filename} needs a real publication date in YYYY-MM-DD format.") from exc
    values["access"] = values["access"].lower()
    if values["access"] not in {"paid", "public excerpt"}:
        raise ValueError(f"Report {filename} must declare Access as 'paid' or 'public excerpt'.")
    return values


def _load_report(filepath: str, filename: str) -> Tuple[Dict[str, Any], List[Tuple[int, str]]]:
    if os.path.getsize(filepath) > MAX_FILE_BYTES:
        raise ValueError(f"Report {filename} exceeds the {MAX_FILE_BYTES // (1024 * 1024)} MB file limit.")

    if filename.lower().endswith(".pdf"):
        metadata_path = os.path.splitext(filepath)[0] + ".json"
        if not os.path.isfile(metadata_path) or os.path.getsize(metadata_path) > 64 * 1024:
            raise ValueError(f"PDF {filename} requires a same-name JSON metadata sidecar under 64 KB.")
        with open(metadata_path, "r", encoding="utf-8") as metadata_file:
            metadata = json.load(metadata_file)
        report = _validate_metadata(metadata, filename)
        reader = PdfReader(filepath, strict=True)
        if len(reader.pages) > MAX_PDF_PAGES:
            raise ValueError(f"PDF {filename} exceeds the {MAX_PDF_PAGES}-page limit.")
        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            page_text = page.extract_text() or ""
            if len(page_text) > MAX_PAGE_CHARS:
                raise ValueError(f"PDF {filename} page {page_number} exceeds the extracted text limit.")
            pages.append((page_number, page_text))
        return report, pages

    with open(filepath, "r", encoding="utf-8") as source_file:
        content = source_file.read()
    metadata = {
        "report_id": (re.search(r"\*\*Report ID:\*\*\s*(R-\d+)", content) or [None, ""])[1],
        "title": (re.search(r"^#\s+(.+)$", content, flags=re.MULTILINE) or [None, ""])[1].strip(),
        "publisher": (re.search(r"\*\*Publisher:\*\*\s*(.+)", content) or [None, ""])[1].strip(),
        "published": (re.search(r"\*\*Publication Date:\*\*\s*(\d{4}-\d{2}-\d{2})", content) or [None, ""])[1],
        "sector": (re.search(r"\*\*Sector:\*\*\s*(.+)", content) or [None, ""])[1].strip(),
        "access": (re.search(r"\*\*Access:\*\*\s*(.+)", content) or [None, ""])[1].strip().lower(),
    }
    report = _validate_metadata(metadata, filename)
    page_parts = re.split(r"<!--\s*Page\s*(\d+)\s*-->", content)
    if len(page_parts) > 1:
        pages = [(int(page_parts[index]), page_parts[index + 1])
                 for index in range(1, len(page_parts), 2)]
    else:
        pages = [(1, content)]
    return report, pages


def ingest_reports(reports_dir: str = None) -> int:
    if not _INGEST_LOCK.acquire(blocking=False):
        raise IngestionBusy("Another report ingestion is already in progress.")
    try:
        return _ingest_reports(reports_dir)
    finally:
        _INGEST_LOCK.release()


def _ingest_reports(reports_dir: str = None) -> int:
    reports_dir = reports_dir or settings.REPORTS_DIR
    if not os.path.isdir(reports_dir):
        raise FileNotFoundError("Configured report directory is unavailable.")
    root = os.path.realpath(reports_dir)
    report_files = sorted(
        filename for filename in os.listdir(root)
        if filename.lower().endswith((".md", ".pdf")) and filename.lower() != "readme.md"
    )
    if len(report_files) > MAX_REPORT_FILES:
        raise ValueError(f"The report directory exceeds the {MAX_REPORT_FILES}-file limit.")

    ids: List[str] = []
    documents: List[str] = []
    metadatas: List[Dict[str, Any]] = []
    report_metadata: List[Dict[str, Any]] = []
    seen_report_ids = set()
    total_file_bytes = 0

    for filename in report_files:
        filepath = os.path.realpath(os.path.join(root, filename))
        if os.path.commonpath([root, filepath]) != root:
            raise ValueError(f"Report path {filename} resolves outside the configured report directory.")
        total_file_bytes += os.path.getsize(filepath)
        if total_file_bytes > MAX_TOTAL_FILE_BYTES:
            raise ValueError(f"The report corpus exceeds the {MAX_TOTAL_FILE_BYTES // (1024 * 1024)} MB total file limit.")
        report, pages = _load_report(filepath, filename)
        report_id = report["report_id"]
        if report_id in seen_report_ids:
            raise ValueError(f"Report ID {report_id} is assigned to more than one file.")
        seen_report_ids.add(report_id)
        report_metadata.append(report)

        report_chunk_count = 0
        for page_number, raw_text in pages:
            safe_text = injection_detector.sanitize_document(report_id, raw_text).strip()
            if not safe_text:
                continue
            year_match = re.search(r"\b20\d{2}\b", safe_text)
            region = "APAC" if re.search(r"Asia-Pacific|\bAPAC\b", safe_text, re.IGNORECASE) else "Global"
            for chunk_number, chunk_text in enumerate(_split_page(safe_text), start=1):
                report_chunk_count += 1
                if len(ids) >= MAX_CHUNKS:
                    raise ValueError(f"The corpus exceeds the {MAX_CHUNKS}-chunk safety limit.")
                ids.append(f"{report_id}_p{page_number}_c{chunk_number}")
                documents.append(chunk_text)
                metadatas.append({
                    "report_id": report_id,
                    "title": report["title"],
                    "sector": report["sector"],
                    "access": report["access"],
                    "page": int(page_number),
                    "region": region,
                    "year": year_match.group(0) if year_match else "unknown",
                })
        if report_chunk_count == 0:
            raise ValueError(f"Report {filename} contains no extractable text; run OCR for scanned PDFs.")

    # Validate the full corpus before changing either persistent store.
    # Stop serving report answers during the cross-store update. If either
    # persistence operation fails, remain unready until a successful retry.
    vector_store.set_ready(False)
    try:
        db_manager.upsert_report_metadata_many(report_metadata)
        vector_store.replace_all_chunks(ids=ids, documents=documents, metadatas=metadatas)
    except Exception:
        logger.exception("Report corpus update failed; report queries remain disabled")
        raise
    vector_store.set_ready(True)
    return len(ids)


if __name__ == "__main__":
    indexed = ingest_reports()
    print(f"Successfully indexed {indexed} report chunks.")
