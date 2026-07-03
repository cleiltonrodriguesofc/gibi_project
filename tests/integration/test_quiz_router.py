"""
Integration tests for the quiz router.

Tests run against the full FastAPI app using TestClient and an
in-memory (file-based) SQLite database configured in conftest.py.
"""
import pytest
from fastapi.testclient import TestClient

from tests.conftest import client  # noqa: F401 — fixture used by pytest


# ---------------------------------------------------------------------------
# GET /api/quiz/perguntas/{capitulo_id}
# ---------------------------------------------------------------------------

class TestGetPerguntas:
    """Tests for the public questions endpoint."""

    def test_returns_questions_for_existing_chapter(self, client: TestClient):
        """Should return question list without resposta_correta field."""
        res = client.get("/api/quiz/perguntas/1")
        assert res.status_code == 200
        data = res.json()
        assert "perguntas" in data
        assert len(data["perguntas"]) > 0

    def test_questions_do_not_expose_correct_answer(self, client: TestClient):
        """resposta_correta must never be included in the response."""
        res = client.get("/api/quiz/perguntas/1")
        assert res.status_code == 200
        for p in res.json()["perguntas"]:
            assert "resposta_correta" not in p
            assert "id" in p
            assert "pergunta" in p
            assert "opcoes" in p

    def test_returns_empty_list_for_nonexistent_chapter(self, client: TestClient):
        """Chapters without quiz data return an empty perguntas list with HTTP 200."""
        res = client.get("/api/quiz/perguntas/999")
        assert res.status_code == 200
        assert res.json()["perguntas"] == []

    def test_questions_have_four_options(self, client: TestClient):
        """Each question should have exactly 4 answer options."""
        res = client.get("/api/quiz/perguntas/1")
        for p in res.json()["perguntas"]:
            assert len(p["opcoes"]) == 4


# ---------------------------------------------------------------------------
# POST /api/quiz/responder
# ---------------------------------------------------------------------------

class TestResponderQuiz:
    """Tests for the answer-submission endpoint."""

    def test_correct_answer_returns_correto_true(self, client: TestClient):
        """Answering correctly should return correto=True."""
        # Cap 1, pergunta 1, resposta_correta = 0
        res = client.post("/api/quiz/responder", json={
            "capitulo_id": 1,
            "pergunta_id": 1,
            "resposta": 0,
        })
        assert res.status_code == 200
        data = res.json()
        assert data["correto"] is True
        assert data["resposta_correta"] == 0

    def test_wrong_answer_returns_correto_false(self, client: TestClient):
        """Answering incorrectly should return correto=False and reveal the right answer."""
        res = client.post("/api/quiz/responder", json={
            "capitulo_id": 1,
            "pergunta_id": 1,
            "resposta": 1,  # wrong answer
        })
        assert res.status_code == 200
        data = res.json()
        assert data["correto"] is False
        assert data["resposta_correta"] == 0

    def test_response_includes_novas_medalhas(self, client: TestClient):
        """Response should always include the novas_medalhas field."""
        res = client.post("/api/quiz/responder", json={
            "capitulo_id": 1,
            "pergunta_id": 1,
            "resposta": 0,
        })
        assert "novas_medalhas" in res.json()

    def test_unknown_chapter_returns_404(self, client: TestClient):
        """Answering a quiz for a chapter with no data returns 404."""
        res = client.post("/api/quiz/responder", json={
            "capitulo_id": 999,
            "pergunta_id": 1,
            "resposta": 0,
        })
        assert res.status_code == 404

    def test_unknown_question_returns_404(self, client: TestClient):
        """Answering a non-existent question within a valid chapter returns 404."""
        res = client.post("/api/quiz/responder", json={
            "capitulo_id": 1,
            "pergunta_id": 999,
            "resposta": 0,
        })
        assert res.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/quiz/concluir
# ---------------------------------------------------------------------------

class TestConcluirCapitulo:
    """Tests for the chapter-completion endpoint."""

    def test_marks_chapter_as_complete(self, client: TestClient):
        """Calling concluir should return ok=True."""
        res = client.post("/api/quiz/concluir", json={"capitulo_id": 1})
        assert res.status_code == 200
        assert res.json()["ok"] is True

    def test_concluir_includes_novas_medalhas(self, client: TestClient):
        """Response must always include novas_medalhas list."""
        res = client.post("/api/quiz/concluir", json={"capitulo_id": 1})
        assert "novas_medalhas" in res.json()

    def test_concluir_unlocks_bronze_medal_after_first_chapter(self, client: TestClient):
        """Completing chapter 1 for the first time should unlock the 'bronze' medal."""
        # Complete chapter 1 to trigger medal check
        res = client.post("/api/quiz/concluir", json={"capitulo_id": 1})
        data = res.json()
        assert "bronze" in data["novas_medalhas"]


# ---------------------------------------------------------------------------
# GET /api/progresso
# ---------------------------------------------------------------------------

class TestGetProgresso:
    """Tests for the progress-query endpoint."""

    def test_returns_empty_for_unknown_session(self, client: TestClient):
        """A fresh session with no cookie should return empty arrays."""
        # Use a clean client with no cookies
        res = client.get("/api/progresso", cookies={})
        assert res.status_code == 200
        data = res.json()
        assert "progresso" in data
        assert "medalhas" in data
