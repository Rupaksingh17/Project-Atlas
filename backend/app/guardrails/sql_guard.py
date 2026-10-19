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

ALLOWED_TABLES = {"reports", "market_metrics"}
ALLOWED_FUNCTIONS = {"count"}

class SQLGuard:
    def validate_and_format(self, query: str) -> str:
        clean = query.strip()
        lower = clean.lower()
        if not clean or re.search(r";|--|#|/\*|\*/", clean):
            raise PermissionError("Security violation: comments and multi-statement SQL are prohibited.")
        
        # Must start with SELECT
        if not lower.startswith("select"):
            raise ValueError("Security violation: Only SELECT queries are permitted.")

        # The report-summary tool only needs simple reads from report metadata.
        # Reject query composition and side-effecting SQL functions instead of
        # trying to make a regular-expression denylist understand all SQL syntax.
        if re.search(r"\b(union|with|into|procedure|handler|call)\b|\(\s*select\b", lower):
            raise PermissionError("Security violation: Composed queries and SQL side effects are prohibited.")

        referenced_tables = re.findall(r"\b(?:from|join)\s+([a-z_][a-z0-9_$]*)", lower)
        if not referenced_tables or any(table not in ALLOWED_TABLES for table in referenced_tables):
            raise PermissionError("Security violation: Queries may read only approved report tables.")

        functions = re.findall(r"\b([a-z_][a-z0-9_$]*)\s*\(", lower)
        if any(function not in ALLOWED_FUNCTIONS for function in functions):
            raise PermissionError("Security violation: SQL function is not permitted.")
            
        # Check disallowed SQL manipulation operations
        for kw in DISALLOWED_KEYWORDS:
            if re.search(kw, lower):
                label = kw.replace(r"\b", "")
                raise PermissionError(f"Security violation: Statement contains forbidden keyword: {label}")
                
        # Enforce max limit of 50 rows
        limit_match = re.search(r"\blimit\s+(\d+)(?:\s+offset\s+\d+)?\s*$", lower)
        if not limit_match:
            clean = f"{clean} LIMIT 50"
        elif int(limit_match.group(1)) > 50:
            clean = re.sub(r"\blimit\s+\d+", "LIMIT 50", clean, count=1, flags=re.IGNORECASE)
            
        return clean

sql_guard = SQLGuard()
