import unittest
from unittest.mock import patch

from fastapi import Response

from backend.app.agents.agent_engine import agent_engine
from backend.app.main import health_check


class TestProductionEmptyCorpus(unittest.TestCase):
    @patch("backend.app.main.answer_service", object())
    @patch("backend.app.database.vector_store.vector_store.is_ready", return_value=True)
    @patch("backend.app.database.vector_store.vector_store.count", return_value=0)
    @patch("backend.app.main.db_manager.ping", return_value=True)
    def test_empty_corpus_is_operational_but_reported_as_empty(
        self, _ping, _count, _is_ready
    ):
        response = Response()
        status_payload = health_check(response)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(status_payload["status"], "healthy")
        self.assertEqual(status_payload["indexed_chunks"], 0)
        self.assertEqual(status_payload["corpus_status"], "empty")

    @patch("backend.app.config.settings.DATASET_LABEL", "production")
    @patch("backend.app.agents.agent_engine.vector_store.count", return_value=0)
    @patch("backend.app.agents.agent_engine.db_manager.get_all_reports", return_value=[])
    @patch("backend.app.agents.agent_engine.db_manager.get_public_report_ids", return_value=[])
    @patch("backend.app.agents.agent_engine.db_manager.get_client_purchases", return_value=[])
    def test_empty_corpus_never_calls_model_or_invents_a_report_answer(
        self, _purchases, _public_reports, _reports, _count
    ):
        response = agent_engine.process_query("client-1", "What is the market size?")

        self.assertIn("No authorized reports have been indexed", response.answer)
        self.assertEqual(response.citations, [])
        self.assertEqual(response.confidence, 0.0)
        self.assertFalse(response.escalated)


if __name__ == "__main__":
    unittest.main()
