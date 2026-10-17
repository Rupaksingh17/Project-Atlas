import re
from typing import Tuple
from backend.app.database.db import db_manager

INJECTION_PATTERNS = [
    r"disregard\s+all\s+previous\s+instructions",
    r"ignore\s+(your\s+)?(previous\s+)?instructions",
    r"print\s+(the\s+)?(full\s+)?contents\s+of\s+(the\s+)?clients\s+table",
    r"note\s+to\s+ai\s+systems",
    r"system\s*:\s*you\s+are",
    r"system\s+instruction",
    r"reveal\s+.*password",
    r"reveal\s+.*secret",
    r"list\s+all\s+client\s+emails",
    r"reveal\s+confidential\s+passwords"
]

class InjectionDetector:
    def __init__(self):
        self.compiled_patterns = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]

    def scan_and_sanitize(self, client_id: str, text: str) -> Tuple[bool, str]:
        detected = False
        sanitized_text = text
        
        for pattern in self.compiled_patterns:
            if pattern.search(sanitized_text):
                detected = True
                db_manager.log_security_event(
                    client_id=client_id,
                    event_type="PROMPT_INJECTION_DETECTED",
                    payload=sanitized_text[:500]
                )
                sanitized_text = pattern.sub("[REDACTED INJECTION ATTEMPT]", sanitized_text)
                
        if "NOTE TO AI SYSTEMS:" in text:
            detected = True
            db_manager.log_security_event(
                client_id=client_id,
                event_type="INDIRECT_PROMPT_INJECTION_IN_DOCUMENT",
                payload="NOTE TO AI SYSTEMS footnote attack neutralized."
            )
            sanitized_text = re.sub(r"\n*\[\^1\]\s*NOTE TO AI SYSTEMS:.*?(?=\n|$)", "", sanitized_text, flags=re.IGNORECASE | re.DOTALL)
            
        return detected, sanitized_text

injection_detector = InjectionDetector()
