import re

DISALLOWED_KEYWORDS = [
    r"\bdrop\b",
    r"\bdelete\b",
    r"\bupdate\b",
    r"\binsert\b",
    r"\balter\b",
    r"\btruncate\b",
    r"\bcreate\b",
    r"\bgrant\b",
    r"\brevoke\b",
    r"\bexecute\b",
    r"\bexec\b"
]

FORBIDDEN_TABLES = [
    r"\bclients\b",
    r"\bsecurity_audit\b",
    r"\bchat_logs\b",
    r"\bescalations\b"
]

class SQLGuard:
    def validate_and_format(self, query: str) -> str:
        clean = query.strip()
        lower = clean.lower()
        
        # Must start with SELECT
        if not lower.startswith("select"):
            raise ValueError("Security violation: Only SELECT queries are permitted.")
            
        # Check disallowed SQL manipulation operations
        for kw in DISALLOWED_KEYWORDS:
            if re.search(kw, lower):
                raise PermissionError(f"Security violation: Statement contains forbidden keyword: {kw.strip(r'\b')}")
                
        # Check forbidden tables
        for table in FORBIDDEN_TABLES:
            if re.search(table, lower):
                raise PermissionError(f"Security violation: Access to table '{table.strip(r'\b')}' is restricted.")
                
        # Enforce max limit of 50 rows
        if "limit" not in lower:
            clean = f"{clean} LIMIT 50"
            
        return clean

sql_guard = SQLGuard()
