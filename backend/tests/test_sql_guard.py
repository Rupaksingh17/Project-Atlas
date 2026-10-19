import unittest

from backend.app.guardrails.sql_guard import sql_guard


class TestSQLGuard(unittest.TestCase):
    def test_allows_report_aggregate_and_applies_limit(self):
        query = "SELECT sector, COUNT(*) FROM reports GROUP BY sector"
        self.assertEqual(
            sql_guard.validate_and_format(query),
            "SELECT sector, COUNT(*) FROM reports GROUP BY sector LIMIT 50",
        )

    def test_rejects_unions_and_nested_selects(self):
        queries = [
            "SELECT id FROM reports UNION SELECT id FROM clients",
            "SELECT id FROM reports WHERE id IN (SELECT id FROM clients)",
        ]
        for query in queries:
            with self.subTest(query=query), self.assertRaises(PermissionError):
                sql_guard.validate_and_format(query)

    def test_rejects_unapproved_tables_and_functions(self):
        queries = [
            "SELECT id FROM clients",
            "SELECT SLEEP(10) FROM reports",
        ]
        for query in queries:
            with self.subTest(query=query), self.assertRaises(PermissionError):
                sql_guard.validate_and_format(query)

    def test_rejects_multiple_statements_and_non_select_statements(self):
        with self.assertRaises(PermissionError):
            sql_guard.validate_and_format("SELECT id FROM reports; DROP TABLE reports")
        with self.assertRaises(ValueError):
            sql_guard.validate_and_format("DELETE FROM reports")


if __name__ == "__main__":
    unittest.main()
