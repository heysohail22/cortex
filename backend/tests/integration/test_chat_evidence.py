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
