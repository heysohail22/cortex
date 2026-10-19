from __future__ import annotations

from unittest.mock import AsyncMock, patch


def test_api_terminal_evidence_response_passes_output_checks():
    from fastapi.testclient import TestClient
    from main import app
    with patch("api.chat.get_native_conversation_turns", AsyncMock(return_value=[])), \
         patch("api.chat.run_crag_async", AsyncMock(return_value={"answer": "No document evidence found.", "source": "guardrail", "route": "no_document_evidence", "evaluation_result": "INCORRECT", "evidence_status": "NONE", "retrieval_corrections_used": 1})), \
         patch("api.chat.save_turn"), patch("api.chat.process_output", return_value=("Checked response", [])) as output:
        response = TestClient(app).post("/api/chat", json={"message": "refund deadline", "session_id": "spec-test"})
    assert response.status_code == 200
    assert response.json()["answer"] == "Checked response"
    assert response.json()["evidence_status"] == "NONE"
    assert response.json()["evaluation_result"] == "INCORRECT"
    output.assert_called_once()


def test_api_invalidates_approval_if_final_scrubbing_changes_answer():
    from fastapi.testclient import TestClient
    from main import app
    dirty = "Use key gsk_1234567890abcdef1234567890abcdef."
    with patch("api.chat.get_native_conversation_turns", AsyncMock(return_value=[])), \
         patch("api.chat.run_crag_async", AsyncMock(return_value={"answer": dirty, "source": "rag", "route": "rag", "citations": ["policy.pdf"], "verification_status": "SUPPORTED", "is_grounded": True, "nli_score": 0.9, "valid_doc_sources": {"policy.pdf"}})), \
         patch("api.chat.save_turn"):
        response = TestClient(app).post("/api/chat", json={"message": "policy", "session_id": "output-scrub-test"})
    assert response.status_code == 200
    result = response.json()
    assert result["verification_status"] == "UNKNOWN"
    assert result["is_grounded"] is None and result["nli_score"] is None
    assert not result["citations"] and "Use key" not in result["answer"]


def test_api_missing_evidence_is_not_called_verified():
    from fastapi.testclient import TestClient
    from main import app
    with patch("api.chat.get_native_conversation_turns", AsyncMock(return_value=[])), \
         patch("api.chat.run_crag_async", AsyncMock(return_value={"answer": "No supporting passages found.", "source": "guardrail", "route": "no_document_evidence", "verification_status": "SKIPPED", "is_grounded": None, "nli_score": None})), \
         patch("api.chat.save_turn"):
        data = TestClient(app).post("/api/chat", json={"message": "policy", "session_id": "no-evidence-status"}).json()
    assert data["verification_status"] == "SKIPPED" and data["is_grounded"] is None
