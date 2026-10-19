from __future__ import annotations

import os
import sys
import unittest


from services.routing import _build_system_prompt, _format_documents


class TestRouterContextFormatting(unittest.TestCase):
    def test_format_documents_with_topics(self):
        docs = [
            {
                "filename": "novacore_handbook.pdf",
                "topics": "Work hours, Remote work, Travel, PTO",
            }
        ]
        formatted = _format_documents(docs)
        self.assertIn('"novacore_handbook.pdf" (Topics: Work hours, Remote work, Travel, PTO)', formatted)

    def test_format_documents_without_topics(self):
        docs = [
            {
                "filename": "document.pdf",
                "topics": "",
            }
        ]
        formatted = _format_documents(docs)
        self.assertIn('"document.pdf"', formatted)
        self.assertNotIn("Topics:", formatted)

    def test_format_documents_string_list(self):
        docs = ["guide.pdf", "architecture.txt"]
        formatted = _format_documents(docs)
        self.assertIn('"guide.pdf"', formatted)
        self.assertIn('"architecture.txt"', formatted)

    def test_build_system_prompt_includes_context(self):
        docs = [
            {
                "filename": "security_policy.pdf",
                "topics": "SEV-1 SLAs, Data Privacy",
            }
        ]
        prompt = _build_system_prompt(has_documents=True, documents=docs)
        self.assertIn('"security_policy.pdf"', prompt)
        self.assertIn("SEV-1 SLAs, Data Privacy", prompt)
        self.assertIn("ALWAYS route to \"rag\"", prompt)

    def test_build_system_prompt_disabled_when_no_docs(self):
        prompt = _build_system_prompt(has_documents=False, documents=[])
        self.assertIn("DISABLED", prompt)
        self.assertNotIn("security_policy.pdf", prompt)


if __name__ == "__main__":
    unittest.main()
