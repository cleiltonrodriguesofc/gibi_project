"""
Quiz and progress router.

Exposes:
  POST /api/quiz/responder  — validate an answer and persist progress
  GET  /api/progresso        — return progress for the current session
  GET  /conquistas           — render the achievements page
"""
import json
import os
import uuid
import logging

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session

from core.infrastructure.database.session import SessionLocal
from core.infrastructure.database.repositories import (
    SQLProgressoRepository,
    SQLMedalhaRepository,
)
from core.domain.entities import Progresso, Medalha

logger = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# ---------------------------------------------------------------------------
# Medal unlock rules: (label, min_chapters_needed, chapters_that_count)
# ---------------------------------------------------------------------------
MEDAL_RULES = [
    ("bronze",   1,  None),   # any 1 chapter
    ("prata",    2,  None),   # any 2 chapters
    ("ouro",     3,  None),   # any 3 chapters
    ("diamante", 4,  None),   # any 4 chapters
]

SESSION_COOKIE = "guardiao_sessao"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _get_or_create_session(request: Request, response: JSONResponse) -> str:
    """Return existing session ID from cookie or mint a new one."""
    sessao_id = request.cookies.get(SESSION_COOKIE)
    if not sessao_id:
        sessao_id = str(uuid.uuid4())
        response.set_cookie(SESSION_COOKIE, sessao_id, max_age=60 * 60 * 24 * 365)
    return sessao_id


def _load_quiz() -> list:
    """Load quiz questions from data/quiz.json."""
    path = os.path.join("data", "quiz.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_capitulos() -> list:
    """Load chapters metadata from data/capitulos.json."""
    path = os.path.join("data", "capitulos.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _check_and_unlock_medals(
    sessao_id: str,
    progresso_repo: SQLProgressoRepository,
    medalha_repo: SQLMedalhaRepository,
) -> list[str]:
    """Unlock any medals the session has just earned. Returns newly unlocked medal names."""
    registros = progresso_repo.get_by_sessao(sessao_id)
    concluidos = [r.capitulo_id for r in registros if r.concluido]
    newly_unlocked = []

    for name, needed, _ in MEDAL_RULES:
        if len(concluidos) >= needed and not medalha_repo.ja_desbloqueada(sessao_id, name):
            medalha_repo.desbloquear(Medalha(sessao_id=sessao_id, medalha=name))
            newly_unlocked.append(name)
            logger.info("Medal '%s' unlocked for session %s", name, sessao_id)

    return newly_unlocked


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/api/quiz/perguntas/{capitulo_id}")
async def get_perguntas(capitulo_id: int):
    """
    Return the quiz questions for a chapter (options only, no correct answer exposed).

    Returns:
        { "perguntas": [{ "id": int, "pergunta": str, "opcoes": [...] }] }
    """
    quiz_data = _load_quiz()
    capitulo_quiz = next((c for c in quiz_data if c["capitulo_id"] == capitulo_id), None)
    if not capitulo_quiz:
        return JSONResponse({"perguntas": []}, status_code=200)

    # Strip resposta_correta before sending to the client
    perguntas_publicas = [
        {"id": p["id"], "pergunta": p["pergunta"], "opcoes": p["opcoes"]}
        for p in capitulo_quiz["perguntas"]
    ]
    return JSONResponse({"perguntas": perguntas_publicas})


# ---------------------------------------------------------------------------
# Answer validation and progress
# ---------------------------------------------------------------------------

@router.post("/api/quiz/responder")
async def responder_quiz(request: Request):
    """
    Validate a quiz answer and persist progress.

    Expected JSON body:
        { "capitulo_id": 1, "pergunta_id": 1, "resposta": 0 }

    Returns:
        { "correto": bool, "resposta_correta": int, "novas_medalhas": [...] }
    """
    body = await request.json()
    capitulo_id: int = body.get("capitulo_id")
    pergunta_id: int = body.get("pergunta_id")
    resposta: int = body.get("resposta")

    # Find the correct answer
    quiz_data = _load_quiz()
    capitulo_quiz = next((c for c in quiz_data if c["capitulo_id"] == capitulo_id), None)
    if not capitulo_quiz:
        return JSONResponse({"erro": "Quiz não encontrado para este capítulo"}, status_code=404)

    pergunta = next((p for p in capitulo_quiz["perguntas"] if p["id"] == pergunta_id), None)
    if not pergunta:
        return JSONResponse({"erro": "Pergunta não encontrada"}, status_code=404)

    correto = resposta == pergunta["resposta_correta"]

    # Persist progress
    sessao_id = request.cookies.get(SESSION_COOKIE, str(uuid.uuid4()))
    novas_medalhas: list[str] = []

    db: Session = SessionLocal()
    try:
        progresso_repo = SQLProgressoRepository(db)
        medalha_repo = SQLMedalhaRepository(db)

        # Upsert progress record for this chapter
        existing = progresso_repo.get_by_sessao_e_capitulo(sessao_id, capitulo_id)
        if existing:
            if correto:
                existing.pontuacao = min(existing.pontuacao + 1, len(capitulo_quiz["perguntas"]))
            progresso_repo.salvar(existing)
        else:
            prog = Progresso(
                sessao_id=sessao_id,
                capitulo_id=capitulo_id,
                concluido=False,
                pontuacao=1 if correto else 0,
            )
            progresso_repo.salvar(prog)

        novas_medalhas = _check_and_unlock_medals(sessao_id, progresso_repo, medalha_repo)
    except Exception as exc:
        logger.error("Error persisting quiz answer: %s", exc)
    finally:
        db.close()

    response = JSONResponse({
        "correto": correto,
        "resposta_correta": pergunta["resposta_correta"],
        "novas_medalhas": novas_medalhas,
    })
    response.set_cookie(SESSION_COOKIE, sessao_id, max_age=60 * 60 * 24 * 365)
    return response


@router.post("/api/quiz/concluir")
async def concluir_capitulo(request: Request):
    """
    Mark a chapter as fully completed (called after quiz is finished).

    Expected JSON body: { "capitulo_id": 1 }

    Returns: { "ok": true, "novas_medalhas": [...] }
    """
    body = await request.json()
    capitulo_id: int = body.get("capitulo_id")

    sessao_id = request.cookies.get(SESSION_COOKIE, str(uuid.uuid4()))
    novas_medalhas: list[str] = []

    db: Session = SessionLocal()
    try:
        progresso_repo = SQLProgressoRepository(db)
        medalha_repo = SQLMedalhaRepository(db)

        existing = progresso_repo.get_by_sessao_e_capitulo(sessao_id, capitulo_id)
        if existing:
            existing.concluido = True
            progresso_repo.salvar(existing)
        else:
            prog = Progresso(sessao_id=sessao_id, capitulo_id=capitulo_id, concluido=True)
            progresso_repo.salvar(prog)

        novas_medalhas = _check_and_unlock_medals(sessao_id, progresso_repo, medalha_repo)
    except Exception as exc:
        logger.error("Error marking chapter as complete: %s", exc)
    finally:
        db.close()

    response = JSONResponse({"ok": True, "novas_medalhas": novas_medalhas})
    response.set_cookie(SESSION_COOKIE, sessao_id, max_age=60 * 60 * 24 * 365)
    return response


@router.get("/api/progresso")
async def get_progresso(request: Request):
    """Return the current session's progress and medals as JSON."""
    sessao_id = request.cookies.get(SESSION_COOKIE, "")
    if not sessao_id:
        return JSONResponse({"progresso": [], "medalhas": []})

    db: Session = SessionLocal()
    try:
        progresso_repo = SQLProgressoRepository(db)
        medalha_repo = SQLMedalhaRepository(db)
        progresso = progresso_repo.get_by_sessao(sessao_id)
        medalhas = medalha_repo.get_by_sessao(sessao_id)
    finally:
        db.close()

    return JSONResponse({
        "progresso": [
            {"capitulo_id": p.capitulo_id, "concluido": p.concluido, "pontuacao": p.pontuacao}
            for p in progresso
        ],
        "medalhas": [m.medalha for m in medalhas],
    })


@router.get("/conquistas", response_class=HTMLResponse)
async def conquistas(request: Request):
    """Render the achievements/medals page for the current session."""
    sessao_id = request.cookies.get(SESSION_COOKIE, "")
    capitulos = _load_capitulos()
    disponiveis = [c for c in capitulos if c.get("disponivel")]

    progresso_list = []
    medalhas_list = []

    if sessao_id:
        db: Session = SessionLocal()
        try:
            progresso_repo = SQLProgressoRepository(db)
            medalha_repo = SQLMedalhaRepository(db)
            progresso_list = progresso_repo.get_by_sessao(sessao_id)
            medalhas_list = medalha_repo.get_by_sessao(sessao_id)
        finally:
            db.close()

    concluidos_ids = {p.capitulo_id for p in progresso_list if p.concluido}
    medalhas_nomes = {m.medalha for m in medalhas_list}

    return templates.TemplateResponse("conquistas.html", {
        "request": request,
        "capitulos_disponiveis": disponiveis,
        "concluidos_ids": concluidos_ids,
        "medalhas": medalhas_nomes,
        "total_disponiveis": len(disponiveis),
        "total_concluidos": len(concluidos_ids),
    })
