import json
import unittest
from unittest.mock import Mock, patch

from backend.app.config import settings
from backend.app.services.llm import GroundedAnswerService, OpenAIAnswerService


class TestAnswerCache(unittest.TestCase):
    def setUp(self):
        self.api_key = settings.OPENAI_API_KEY
        self.output_limit = settings.LLM_MAX_OUTPUT_TOKENS
        settings.OPENAI_API_KEY = "unit-test-key"
        settings.LLM_MAX_OUTPUT_TOKENS = 333
        self.service = OpenAIAnswerService()
        self.chunks = [{
            "text": "The market was USD 4.21 billion in 2024.",
            "metadata": {"report_id": "R-201", "page": 1},
            "score": 0.91,
        }]

    def tearDown(self):
        settings.OPENAI_API_KEY = self.api_key
        settings.LLM_MAX_OUTPUT_TOKENS = self.output_limit

    @patch("backend.app.services.llm.requests.post")
    def test_repeated_question_reuses_answer_and_enforces_token_cap(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "answer": "USD 4.21 billion.",
                "source_numbers": [1],
                "confidence": 0.95,
                "conflicts": [],
            })}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        }
        post.return_value = response

        first = self.service.answer("What was the market size?", self.chunks)
        second = self.service.answer("  WHAT was the market size?  ", self.chunks)

        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.kwargs["json"]["max_tokens"], 333)
        self.assertEqual(first["tokens"], 120)
        self.assertEqual(second["tokens"], 0)
        self.assertEqual(second["cost"], 0.0)
        self.assertEqual(second["sources"][0]["metadata"]["report_id"], "R-201")

    @patch("backend.app.services.llm.requests.post")
    def test_different_source_evidence_does_not_reuse_cached_answer(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "choices": [{"message": {"content": json.dumps({
                "answer": "USD 4.21 billion.",
                "source_numbers": [1],
                "confidence": 0.95,
                "conflicts": [],
            })}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 20, "total_tokens": 120},
        }
        post.return_value = response

        self.service.answer("What was the market size?", self.chunks)
        changed = [dict(self.chunks[0], text="The market was USD 5 billion in 2024.")]
        self.service.answer("What was the market size?", changed)

        self.assertEqual(post.call_count, 2)

    @patch("backend.app.services.llm.settings.LLM_PROVIDER", "ollama")
    @patch("backend.app.services.llm.settings.OLLAMA_BASE_URL", "http://host.docker.internal:11434")
    @patch("backend.app.services.llm.requests.post")
    def test_local_ollama_provider_requires_no_api_key_and_has_zero_cost(self, post):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "message": {"content": json.dumps({
                "answer": "USD 4.21 billion.",
                "source_numbers": [1],
                "confidence": 0.95,
                "conflicts": [],
            })},
            "prompt_eval_count": 100,
            "eval_count": 20,
        }
        post.return_value = response
        service = GroundedAnswerService()

        result = service.answer("What was the market size?", self.chunks)

        self.assertEqual(post.call_args.args[0], "http://host.docker.internal:11434/api/chat")
        self.assertEqual(post.call_args.kwargs["json"]["format"], "json")
        self.assertEqual(post.call_args.kwargs["json"]["options"]["num_predict"], 333)
        self.assertEqual(result["tokens"], 120)
        self.assertEqual(result["cost"], 0.0)
        self.assertEqual(result["sources"][0]["metadata"]["report_id"], "R-201")


if __name__ == "__main__":
    unittest.main()
