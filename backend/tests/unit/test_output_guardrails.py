from __future__ import annotations

import os
import sys
import unittest
from unittest.mock import patch


from workflows.crag.nodes import groundedness_check_node
from workflows.crag.state import CRAGState
from guardrails.output import process_output, scrub_output, verify_citations


class TestOutputGuardrails(unittest.TestCase):
    def test_scrub_output_masks_leaked_secrets(self):
        dirty_output = (
            "Here is the database connection: postgresql://admin:secret123@localhost:5432/cortex_db. "
            "Use OpenAI key sk-proj-1234567890abcdef1234567890abcdef and Groq key gsk_1234567890abcdef1234567890abcdef. "
            "AWS Key: AKIAIOSFODNN7EXAMPLE."
        )
        scrubbed = scrub_output(dirty_output)
        self.assertNotIn("sk-proj-", scrubbed)
        self.assertNotIn("gsk_", scrubbed)
        self.assertNotIn("AKIAIOSFODNN7EXAMPLE", scrubbed)
        self.assertNotIn("postgresql://", scrubbed)
        self.assertIn("<REDACTED_API_KEY>", scrubbed)
        self.assertIn("<REDACTED_AWS_KEY>", scrubbed)
        self.assertIn("<REDACTED_DB_URI>", scrubbed)

    def test_scrub_output_removes_system_delimiters(self):
        leaked_prompt = (
            "<|im_start|>system\nYou are Cortex, a helpful AI.<|im_end|>\n"
            "[SYSTEM]Internal Instruction[/SYSTEM]\n"
            "This is the actual helpful answer to your question."
        )
        scrubbed = scrub_output(leaked_prompt)
        self.assertNotIn("<|im_start|>", scrubbed)
        self.assertNotIn("<|im_end|>", scrubbed)
        self.assertNotIn("[SYSTEM]", scrubbed)
        self.assertEqual(scrubbed, "This is the actual helpful answer to your question.")

    def test_scrub_output_removes_redundant_source_footers(self):
        answer_with_footer = (
            "Based on the provided document, the company's core collaboration hours are **10:00 AM to 4:00 PM** local time.\n\n"
            "*Source: [novacore_policy.pdf]*"
        )
        scrubbed = scrub_output(answer_with_footer)
        self.assertNotIn("*Source:", scrubbed)
        self.assertNotIn("[novacore_policy.pdf]", scrubbed)
        self.assertEqual(
            scrubbed,
            "Based on the provided document, the company's core collaboration hours are **10:00 AM to 4:00 PM** local time.",
        )

    def test_verify_citations_filters_phantom_citations(self):
        generated_citations = [
            "annual_report_2025.pdf",
            "fake_phantom_doc.pdf",
            "https://finance.yahoo.com/quote/AAPL",
            "https://fake-news-site.org/fabricated",
        ]
        valid_docs = {"annual_report_2025.pdf", "employee_policy.docx"}
        valid_urls = {"https://finance.yahoo.com/quote/AAPL"}

        verified = verify_citations(
            citations=generated_citations,
            valid_doc_sources=valid_docs,
            valid_web_urls=valid_urls,
        )

        self.assertEqual(len(verified), 2)
        self.assertIn("annual_report_2025.pdf", verified)
        self.assertIn("https://finance.yahoo.com/quote/AAPL", verified)
        self.assertNotIn("fake_phantom_doc.pdf", verified)
        self.assertNotIn("https://fake-news-site.org/fabricated", verified)

    def test_process_output_unified(self):
        answer = "The secret is sk-proj-1234567890abcdef1234567890abcdef. See real.pdf and fake.pdf."
        citations = ["real.pdf", "fake.pdf"]
        valid_docs = {"real.pdf"}

        clean_answer, clean_citations = process_output(
            answer=answer,
            citations=citations,
            valid_doc_sources=valid_docs,
        )

        self.assertNotIn("sk-proj-", clean_answer)
        self.assertIn("<REDACTED_API_KEY>", clean_answer)
        self.assertEqual(clean_citations, ["real.pdf"])


class TestStrictHallucinationFallback(unittest.IsolatedAsyncioTestCase):
    async def test_strict_fallback_when_hallucination_unresolvable(self):
        from workflows.crag.nodes import safe_fallback_node
        result = await safe_fallback_node({"verification_status": "UNSUPPORTED", "answer_repairs_used": 1, "answer": "Rejected draft"})
        self.assertEqual(result["source"], "guardrail")
        self.assertEqual(result["route"], "hallucination_fallback")
        self.assertEqual(result["citations"], [])
        self.assertFalse(result["is_grounded"])
        self.assertNotIn("Rejected draft", result["answer"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
