import os
import sqlite3
import logging
from typing import List, Dict, Any, Optional
import pymysql
from pymysql.cursors import DictCursor
from backend.app.config import settings
from backend.app.guardrails.sql_guard import sql_guard

logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.use_mysql = False
        self._init_connection()

    def _init_connection(self):
        if not settings.ALLOW_SQLITE_FALLBACK:
            # Do not make import-time DB availability a prerequisite for starting the API.
            self.use_mysql = True
            return
        try:
            conn = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                connect_timeout=3,
                read_timeout=10,
                write_timeout=10,
                cursorclass=DictCursor
            )
            conn.close()
            self.use_mysql = True
        except Exception:
            logger.warning("MySQL is unavailable; using explicitly enabled SQLite fallback.", exc_info=True)
            self.use_mysql = False
            self._init_sqlite()

    def _init_sqlite(self):
        self.sqlite_path = settings.SQLITE_PATH
        os.makedirs(os.path.dirname(self.sqlite_path), exist_ok=True)
        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                publisher TEXT NOT NULL,
                published TEXT NOT NULL,
                sector TEXT NOT NULL,
                access TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS market_metrics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                report_id TEXT NOT NULL,
                metric TEXT NOT NULL,
                region TEXT NOT NULL,
                year_period TEXT NOT NULL,
                value TEXT NOT NULL,
                scope_note TEXT
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS clients (
                id TEXT PRIMARY KEY,
                company TEXT NOT NULL,
                contact_email TEXT NOT NULL,
                purchased_reports TEXT NOT NULL
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS escalations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                query TEXT NOT NULL,
                reason TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                status TEXT DEFAULT 'open',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS chat_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                query TEXT NOT NULL,
                answer TEXT NOT NULL,
                confidence REAL DEFAULT 0.0,
                escalated INTEGER DEFAULT 0,
                latency_ms INTEGER DEFAULT 0,
                tokens_used INTEGER DEFAULT 0,
                estimated_cost_usd REAL,
                feedback TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        chat_columns = {row[1] for row in cursor.execute("PRAGMA table_info(chat_logs)").fetchall()}
        if "tokens_used" not in chat_columns:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN tokens_used INTEGER DEFAULT 0")
        if "estimated_cost_usd" not in chat_columns:
            cursor.execute("ALTER TABLE chat_logs ADD COLUMN estimated_cost_usd REAL")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed fictional records only when the isolated assignment demo is explicitly selected.
        cursor.execute("SELECT COUNT(*) FROM reports")
        if settings.DATASET_LABEL == "assignment_demo_fictional" and cursor.fetchone()[0] == 0:
            reports_data = [
                ('R-101', 'Global Smart Water Meter Market 2025', 'CMR', '2025-03-10', 'Utilities', 'paid'),
                ('R-102', 'Smart Water Metering: Industry Outlook 2024', 'Aquila Insights (third party)', '2024-06-18', 'Utilities', 'public excerpt'),
                ('R-103', 'Residential Water Purifier Market 2025', 'CMR', '2025-01-22', 'Consumer Durables', 'paid'),
                ('R-104', 'Industrial IoT Sensors Market 2025', 'CMR', '2025-02-15', 'Manufacturing', 'paid'),
                ('R-105', 'Commercial Water Treatment Systems 2024', 'Aquila Insights (third party)', '2024-11-05', 'Utilities', 'paid'),
                ('R-106', 'Smart Gas Metering Infrastructure 2025', 'CMR', '2025-04-12', 'Energy', 'paid')
            ]
            cursor.executemany("INSERT INTO reports VALUES (?, ?, ?, ?, ?, ?)", reports_data)
            
            metrics_data = [
                (1, 'R-101', 'Market size', 'Global', '2024', 'USD 4.21 B', 'Includes hardware, software and services'),
                (2, 'R-101', 'CAGR', 'Global', '2025-2030', '11.2 %', 'Forecast period stated as 2025-2030'),
                (3, 'R-101', 'Regional share', 'APAC', '2024', '38 %', 'Share of global market size'),
                (4, 'R-102', 'Market size', 'Global', '2024', 'USD 3.87 B', 'AMR / AMI hardware only'),
                (5, 'R-102', 'CAGR', 'Global', '2024-2029', '9.8 %', 'Different forecast window from R-101'),
                (6, 'R-102', 'Regional share', 'APAC', '2024', '41 %', 'Share of hardware market'),
                (7, 'R-103', 'Market size', 'Global', '2024', 'USD 9.15 B', 'Residential point-of-use systems'),
                (8, 'R-104', 'Market size', 'Global', '2024', 'USD 14.60 B', 'Factory automation sensors'),
                (9, 'R-105', 'Market size', 'Global', '2024', 'USD 5.30 B', 'Commercial membrane filtration'),
                (10, 'R-106', 'Market size', 'Global', '2024', 'USD 2.95 B', 'Smart gas telemetry')
            ]
            cursor.executemany("INSERT INTO market_metrics VALUES (?, ?, ?, ?, ?, ?, ?)", metrics_data)
            
            clients_data = [
                ('C-01', 'Northwind Utilities', 'ops@example.com', 'R-101, R-103'),
                ('C-02', 'Blue Delta Infra', 'procurement@example.com', 'R-103')
            ]
            cursor.executemany("INSERT INTO clients VALUES (?, ?, ?, ?)", clients_data)
        
        conn.commit()
        conn.close()

    def get_connection(self, readonly: bool = False):
        if self.use_mysql:
            user = settings.READONLY_DB_USER if readonly else settings.DB_USER
            pwd = settings.READONLY_DB_PASSWORD if readonly else settings.DB_PASSWORD
            return pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=user,
                password=pwd,
                database=settings.DB_NAME,
                connect_timeout=3,
                read_timeout=10,
                write_timeout=10,
                cursorclass=DictCursor
            )
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def get_client_purchases(self, client_id: str) -> List[str]:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            query = "SELECT purchased_reports FROM clients WHERE id = %s" if self.use_mysql else "SELECT purchased_reports FROM clients WHERE id = ?"
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            if not row:
                return []
            raw = row['purchased_reports'] if isinstance(row, dict) else row[0]
            purchased = [item.strip() for item in raw.split(',') if item.strip()]
            return purchased
        except Exception:
            logger.exception("Could not resolve client report entitlements")
            raise
        finally:
            conn.close()

    def get_public_report_ids(self) -> List[str]:
        conn = self.get_connection(readonly=True)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM reports WHERE access = 'public excerpt'")
            rows = cursor.fetchall()
            return [str(row["id"] if isinstance(row, dict) else row[0]) for row in rows]
        finally:
            conn.close()

    def client_exists(self, client_id: str) -> bool:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            query = "SELECT 1 FROM clients WHERE id = %s" if self.use_mysql else "SELECT 1 FROM clients WHERE id = ?"
            cursor.execute(query, (client_id,))
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def ping(self) -> bool:
        conn = self.get_connection(readonly=True)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            return cursor.fetchone() is not None
        finally:
            conn.close()

    def get_all_reports(self) -> List[Dict[str, Any]]:
        conn = self.get_connection(readonly=True)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, publisher, published, sector, access FROM reports")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def upsert_report_metadata(self, metadata: Dict[str, Any]) -> None:
        self.upsert_report_metadata_many([metadata])

    def upsert_report_metadata_many(self, reports: List[Dict[str, Any]]) -> None:
        if not reports:
            return
        values = [(
            report["report_id"], report["title"], report["publisher"],
            report["published"], report["sector"], report["access"],
        ) for report in reports]
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            if self.use_mysql:
                cursor.executemany(
                    "INSERT INTO reports (id,title,publisher,published,sector,access) VALUES (%s,%s,%s,%s,%s,%s) "
                    "ON DUPLICATE KEY UPDATE title=VALUES(title),publisher=VALUES(publisher),published=VALUES(published),sector=VALUES(sector),access=VALUES(access)",
                    values,
                )
            else:
                cursor.executemany(
                    "INSERT INTO reports (id,title,publisher,published,sector,access) VALUES (?,?,?,?,?,?) "
                    "ON CONFLICT(id) DO UPDATE SET title=excluded.title,publisher=excluded.publisher,published=excluded.published,sector=excluded.sector,access=excluded.access",
                    values,
                )
            conn.commit()
        except Exception:
            conn.rollback()
            logger.exception("Report metadata update failed")
            raise
        finally:
            conn.close()

    def execute_readonly_query(self, sql_query: str, params: tuple = ()) -> List[Dict[str, Any]]:
        safe_query = sql_guard.validate_and_format(sql_query)
        conn = self.get_connection(readonly=True)
        try:
            cursor = conn.cursor()
            cursor.execute(safe_query, params)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def create_escalation(self, client_id: str, query: str, reason: str, confidence: float = 0.0) -> int:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            if self.use_mysql:
                sql = "INSERT INTO escalations (client_id, query, reason, confidence) VALUES (%s, %s, %s, %s)"
                cursor.execute(sql, (client_id, query, reason, confidence))
                conn.commit()
                return cursor.lastrowid
            else:
                sql = "INSERT INTO escalations (client_id, query, reason, confidence) VALUES (?, ?, ?, ?)"
                cursor.execute(sql, (client_id, query, reason, confidence))
                conn.commit()
                return cursor.lastrowid
        finally:
            conn.close()

    def get_escalations(self) -> List[Dict[str, Any]]:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, client_id, query, reason, confidence, status, created_at FROM escalations ORDER BY id DESC")
            rows = cursor.fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def log_chat(self, client_id: str, query: str, answer: str, confidence: float, escalated: bool, latency_ms: int, tokens_used: int = 0, estimated_cost_usd: Optional[float] = None) -> int:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            esc_val = 1 if escalated else 0
            if self.use_mysql:
                sql = "INSERT INTO chat_logs (client_id, query, answer, confidence, escalated, latency_ms, tokens_used, estimated_cost_usd) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (client_id, query, answer, confidence, esc_val, latency_ms, tokens_used, estimated_cost_usd))
            else:
                sql = "INSERT INTO chat_logs (client_id, query, answer, confidence, escalated, latency_ms, tokens_used, estimated_cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?)"
                cursor.execute(sql, (client_id, query, answer, confidence, esc_val, latency_ms, tokens_used, estimated_cost_usd))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            logger.exception("Chat response could not be persisted")
            raise
        finally:
            conn.close()

    def update_feedback(self, chat_id: int, client_id: str, feedback: str) -> bool:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            ownership_query = "SELECT 1 FROM chat_logs WHERE id = %s AND client_id = %s" if self.use_mysql else "SELECT 1 FROM chat_logs WHERE id = ? AND client_id = ?"
            cursor.execute(ownership_query, (chat_id, client_id))
            if cursor.fetchone() is None:
                return False
            if self.use_mysql:
                cursor.execute("UPDATE chat_logs SET feedback = %s WHERE id = %s AND client_id = %s", (feedback, chat_id, client_id))
            else:
                cursor.execute("UPDATE chat_logs SET feedback = ? WHERE id = ? AND client_id = ?", (feedback, chat_id, client_id))
            conn.commit()
            return True
        finally:
            conn.close()

    def log_security_event(self, client_id: str, event_type: str, payload: str):
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            if self.use_mysql:
                cursor.execute("INSERT INTO security_audit (client_id, event_type, payload) VALUES (%s, %s, %s)", (client_id, event_type, payload))
            else:
                cursor.execute("INSERT INTO security_audit (client_id, event_type, payload) VALUES (?, ?, ?)", (client_id, event_type, payload))
            conn.commit()
        except Exception:
            logger.exception("Security audit event could not be persisted")
            return False
        finally:
            conn.close()

db_manager = DatabaseManager()
