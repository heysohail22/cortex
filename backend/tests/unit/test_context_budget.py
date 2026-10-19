from __future__ import annotations

import os
import sys
import unittest


from services.generation import build_doc_context, build_web_context
from providers.tavily import _clean_web_results


class TestContextBudgetAndFormatting(unittest.TestCase):
    def test_build_doc_context_budget_capping(self):
        # Create 10 large chunks totaling 15,000 characters
        large_chunks = [
            {"source": f"doc_{i}.pdf", "text": "A" * 1500}
            for i in range(10)
        ]

        # Cap at 4,000 characters
        context = build_doc_context(large_chunks, max_chars=4000)
        self.assertLessEqual(len(context), 4100)
        self.assertIn("doc_0.pdf", context)
        self.assertIn("doc_1.pdf", context)
        # Verify later chunks were omitted due to budget
        self.assertNotIn("doc_9.pdf", context)

    def test_build_web_context_snippet_and_budget_capping(self):
        # Create 5 web results with long content
        web_results = [
            {
                "title": f"Article {i}",
                "url": f"https://example.com/article_{i}",
                "content": "Word " * 500,  # ~2,500 chars
            }
            for i in range(5)
        ]

        # Individual snippet capped at 300 chars, total context capped at 1,000 chars
        context = build_web_context(web_results, max_chars=1000, max_snippet_chars=300)
        self.assertLessEqual(len(context), 1100)
        self.assertIn("[Web Source 1: Article 0]", context)
        self.assertIn("URL: https://example.com/article_0", context)
        # Verify snippet truncation
        self.assertIn("...", context)
        # Verify 5th article omitted to respect total budget
        self.assertNotIn("Article 4", context)

    def test_clean_web_results_extracts_only_clean_fields(self):
        raw_tavily_results = [
            {
                "title": "Clean Title 1",
                "url": "https://example.com/page1",
                "content": "This is relevant    factual   summary text.\n\nWith extra lines.",
                "raw_content": "<html><body><h1>Massive Raw Scrape</h1></body></html>",
                "images": ["https://example.com/img1.png"],
                "score": 0.88,
            },
            {
                # Duplicate URL
                "title": "Duplicate Title",
                "url": "https://example.com/page1",
                "content": "Duplicate content",
            },
            {
                "title": "Clean Title 2",
                "url": "https://example.com/page2",
                "content": "Second clean snippet.",
                "score": 0.75,
            },
        ]

        cleaned = _clean_web_results(raw_tavily_results)
        self.assertEqual(len(cleaned), 2)  # Duplicate filtered out

        first = cleaned[0]
        self.assertEqual(first["title"], "Clean Title 1")
        self.assertEqual(first["url"], "https://example.com/page1")
        self.assertEqual(first["content"], "This is relevant factual summary text. With extra lines.")
        self.assertEqual(first["score"], 0.88)
        self.assertNotIn("raw_content", first)
        self.assertNotIn("images", first)


if __name__ == "__main__":
    unittest.main(verbosity=2)
