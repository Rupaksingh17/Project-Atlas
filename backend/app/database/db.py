import os
import sqlite3
from typing import List, Dict, Any, Optional
import pymysql
from pymysql.cursors import DictCursor
from backend.app.config import settings

class DatabaseManager:
    def __init__(self):
        self.use_mysql = False
        self._init_connection()

    def _init_connection(self):
        try:
            conn = pymysql.connect(
                host=settings.DB_HOST,
                port=settings.DB_PORT,
                user=settings.DB_USER,
                password=settings.DB_PASSWORD,
                database=settings.DB_NAME,
                connect_timeout=3,
                cursorclass=DictCursor
            )
            conn.close()
            self.use_mysql = True
        except Exception:
            self.use_mysql = False
            self._init_sqlite()

    def _init_sqlite(self):
        self.sqlite_path = os.path.join(os.path.dirname(__file__), "..", "..", "atlas_local.db")
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
                feedback TEXT DEFAULT 'none',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS security_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                client_id TEXT NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Seed initial data if empty
        cursor.execute("SELECT COUNT(*) FROM reports")
        if cursor.fetchone()[0] == 0:
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
                cursorclass=DictCursor
            )
        else:
            conn = sqlite3.connect(self.sqlite_path)
            conn.row_factory = sqlite3.Row
            return conn

    def get_client_purchases(self, client_id: str) -> List[str]:
        try:
            conn = self.get_connection(readonly=False)
            cursor = conn.cursor()
            query = "SELECT purchased_reports FROM clients WHERE id = %s" if self.use_mysql else "SELECT purchased_reports FROM clients WHERE id = ?"
            cursor.execute(query, (client_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return []
            raw = row['purchased_reports'] if isinstance(row, dict) else row[0]
            purchased = [item.strip() for item in raw.split(',') if item.strip()]
            return purchased
        except Exception:
            return []

    def get_all_reports(self) -> List[Dict[str, Any]]:
        try:
            conn = self.get_connection(readonly=True)
            cursor = conn.cursor()
            cursor.execute("SELECT id, title, publisher, published, sector, access FROM reports")
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
        except Exception:
            return []

    def execute_readonly_query(self, sql_query: str) -> List[Dict[str, Any]]:
        sql_clean = sql_query.strip().lower()
        if not sql_clean.startswith("select"):
            raise ValueError("Only SELECT queries are permitted on the read-only interface.")
        
        # Block access to confidential clients table
        if "clients" in sql_clean:
            raise PermissionError("Access to the clients table is strictly prohibited.")
            
        conn = self.get_connection(readonly=True)
        try:
            cursor = conn.cursor()
            cursor.execute(sql_query)
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

    def log_chat(self, client_id: str, query: str, answer: str, confidence: float, escalated: bool, latency_ms: int) -> int:
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            esc_val = 1 if escalated else 0
            if self.use_mysql:
                sql = "INSERT INTO chat_logs (client_id, query, answer, confidence, escalated, latency_ms) VALUES (%s, %s, %s, %s, %s, %s)"
                cursor.execute(sql, (client_id, query, answer, confidence, esc_val, latency_ms))
            else:
                sql = "INSERT INTO chat_logs (client_id, query, answer, confidence, escalated, latency_ms) VALUES (?, ?, ?, ?, ?, ?)"
                cursor.execute(sql, (client_id, query, answer, confidence, esc_val, latency_ms))
            conn.commit()
            return cursor.lastrowid
        except Exception:
            return 0
        finally:
            conn.close()

    def update_feedback(self, chat_id: int, feedback: str):
        conn = self.get_connection(readonly=False)
        try:
            cursor = conn.cursor()
            if self.use_mysql:
                cursor.execute("UPDATE chat_logs SET feedback = %s WHERE id = %s", (feedback, chat_id))
            else:
                cursor.execute("UPDATE chat_logs SET feedback = ? WHERE id = ?", (feedback, chat_id))
            conn.commit()
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
            pass
        finally:
            conn.close()

db_manager = DatabaseManager()
