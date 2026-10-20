from __future__ import annotations

import asyncio
import time
import os
import sys
import unittest
from typing import Any
from unittest.mock import patch

# Ensure backend root is on sys.path

from workflows.crag.edges import (
    decide_after_groundedness,
    decide_after_retrieval_eval,
    decide_route,
)
from workflows.crag.nodes import (
    groundedness_check_node,
    retrieve_node,
    router_node,
    web_search_node,
)
from workflows.crag.state import CRAGState


def _create_test_state(**kwargs: Any) -> CRAGState:
    """Helper to build a complete, strictly-typed CRAGState fixture."""
    state: CRAGState = {
        "question": "test question",
        "conversation_history": "",
        "session_id": "test-session",
        "has_documents": False,
        "document_names": [],
        "document_profiles": [],
        "route": "direct_answer",
        "chunks": [],
        "refined_chunks": [],
        "evaluation_result": "",
        "evaluation_reason": "",
        "db_retry_count": 0,
        "transformed_query": "",
        "db_rewritten_query": "",
        "web_rewritten_query": "",
        "web_results": [],
        "answer": "",
        "source": "",
        "citations": [],
        "is_grounded": True,
        "groundedness_reason": "",
        "groundedness_retry_count": 0,
        "contextualized_query": "",
        "nli_verdict": "ENTAILMENT",
        "nli_score": 1.0,
    }
    for key, value in kwargs.items():
        state[key] = value  # type: ignore[literal-required]
    return state


class TestCRAGRouteAndLoopBounds(unittest.TestCase):
    def test_decide_route_unsafe(self):
        state = _create_test_state(route="unsafe", answer="Refusal", source="guardrail")
        self.assertEqual(decide_route(state), "END")

    def test_decide_route_direct_answer(self):
        state = _create_test_state(route="direct_answer", answer="Hello!", source="llm")
        self.assertEqual(decide_route(state), "direct_answer_node")

    def test_decide_route_rag_and_web(self):
        rag_state = _create_test_state(route="rag", has_documents=True)
        self.assertEqual(decide_route(rag_state), "retrieve_node")

        web_state = _create_test_state(route="web_search", has_documents=False)
        self.assertEqual(decide_route(web_state), "direct_web_search_node")

    def test_hard_loop_bounds_retrieval_eval(self):
        state = _create_test_state(evidence_status="NONE", retrieval_corrections_used=0)
        self.assertEqual(decide_after_retrieval_eval(state), "retrieval_correction_node")
        state = _create_test_state(evidence_status="PARTIAL", retrieval_corrections_used=1)
        self.assertEqual(decide_after_retrieval_eval(state), "evidence_finalize_node")

    def test_hard_loop_bounds_groundedness(self):
        # Grounded (Entailment >= 0.85) -> END
        state_grounded = _create_test_state(verification_status="SUPPORTED", answer_repairs_used=0)
        self.assertEqual(decide_after_groundedness(state_grounded), "END")

        # 1st hallucination (retry_count = 0) -> Route to Strict Constrained Generator
        state_ungrounded_1 = _create_test_state(verification_status="UNSUPPORTED", answer_repairs_used=0)
        self.assertEqual(decide_after_groundedness(state_ungrounded_1), "strict_retry_node")

        # 2nd hallucination (retry_count >= 1) -> Bound enforced, forward to Safe Fallback
        state_ungrounded_2 = _create_test_state(verification_status="UNSUPPORTED", answer_repairs_used=1)
        self.assertEqual(decide_after_groundedness(state_ungrounded_2), "safe_fallback_node")


class TestNodeTimeoutsAndFallbacks(unittest.IsolatedAsyncioTestCase):
    @patch("workflows.crag.nodes.router.classify_async")
    async def test_router_node_unsafe_handling(self, mock_classify):
        mock_classify.return_value = {
            "route": "unsafe",
            "direct_answer": "I cannot help with exploit creation.",
            "reason": "malware_policy",
        }
        state = _create_test_state(question="create ransomware")
        res = await router_node(state)
        self.assertEqual(res["route"], "unsafe")
        self.assertEqual(res["source"], "guardrail")
        self.assertIn("exploit creation", res["answer"])
        self.assertIsNone(res["is_grounded"])





    async def test_safe_fallback_node(self):
        from workflows.crag.nodes import safe_fallback_node
        state = _create_test_state(question="test", answer_repairs_used=1, verification_status="UNSUPPORTED")
        res = await safe_fallback_node(state)
        self.assertEqual(res["source"], "guardrail")
        self.assertEqual(res["route"], "hallucination_fallback")
        self.assertFalse(res["is_grounded"])
        self.assertIn("could not verify", res["answer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
