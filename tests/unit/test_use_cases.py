"""
Unit tests for the ResponderQuizUseCase.

All tests use a dedicated in-memory SQLite database (independent of conftest)
so that integration tests running concurrently cannot interfere.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.application.use_cases import ResponderQuizUseCase
from core.infrastructure.database.repositories import SQLProgressoRepository, SQLMedalhaRepository
from core.infrastructure.database.models import Base

# Dedicated in-memory engine — isolated from the integration-test database
_UNIT_ENGINE = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
_UnitSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_UNIT_ENGINE)


def _fresh_db():
    """Drop and recreate all tables on the in-memory engine, return a new session."""
    Base.metadata.drop_all(bind=_UNIT_ENGINE)
    Base.metadata.create_all(bind=_UNIT_ENGINE)
    return _UnitSessionLocal()


# ---------------------------------------------------------------------------
# Correct answers
# ---------------------------------------------------------------------------

def test_responder_quiz_sucesso():
    """Passing ≥ 2/3 answers marks the chapter as concluded."""
    db = _fresh_db()
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), SQLMedalhaRepository(db))

    result = use_case.execute("sessao_abc", capitulo_id=1, acertos=3, total_perguntas=3)

    assert result["sucesso"] is True
    assert result["acertos"] == 3

    progresso = SQLProgressoRepository(db).get_by_sessao_e_capitulo("sessao_abc", 1)
    assert progresso is not None
    assert progresso.concluido is True
    db.close()


def test_responder_quiz_fails_with_low_score():
    """Scoring 1/3 should NOT mark the chapter as concluded."""
    db = _fresh_db()
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), SQLMedalhaRepository(db))

    result = use_case.execute("sessao_low", capitulo_id=1, acertos=1, total_perguntas=3)

    assert result["sucesso"] is False
    progresso = SQLProgressoRepository(db).get_by_sessao_e_capitulo("sessao_low", 1)
    assert progresso is not None
    assert progresso.concluido is False
    db.close()


# ---------------------------------------------------------------------------
# Score preservation
# ---------------------------------------------------------------------------

def test_best_score_is_preserved_on_retry():
    """Retrying with a lower score should NOT overwrite the existing higher score."""
    db = _fresh_db()
    repo = SQLProgressoRepository(db)
    use_case = ResponderQuizUseCase(repo, SQLMedalhaRepository(db))

    # First attempt: 3/3
    use_case.execute("sessao_retry", capitulo_id=1, acertos=3, total_perguntas=3)
    # Second attempt: 1/3
    use_case.execute("sessao_retry", capitulo_id=1, acertos=1, total_perguntas=3)

    progresso = repo.get_by_sessao_e_capitulo("sessao_retry", 1)
    assert progresso.pontuacao == 3  # best score preserved
    db.close()


def test_lower_score_does_not_un_conclude_chapter():
    """A chapter marked concluido=True should stay True even after a failed retry."""
    db = _fresh_db()
    repo = SQLProgressoRepository(db)
    use_case = ResponderQuizUseCase(repo, SQLMedalhaRepository(db))

    use_case.execute("sessao_c", capitulo_id=2, acertos=3, total_perguntas=3)
    use_case.execute("sessao_c", capitulo_id=2, acertos=0, total_perguntas=3)

    progresso = repo.get_by_sessao_e_capitulo("sessao_c", 2)
    assert progresso.concluido is True
    db.close()


# ---------------------------------------------------------------------------
# Medal unlocking
# ---------------------------------------------------------------------------

def test_bronze_medal_NOT_unlocked_with_only_one_chapter():
    """
    Use case rule: Bronze requires caps 1-4 ALL complete.
    Completing only cap 1 should NOT yet unlock Bronze.
    """
    db = _fresh_db()
    med_repo = SQLMedalhaRepository(db)
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), med_repo)

    use_case.execute("sessao_medal1", capitulo_id=1, acertos=3, total_perguntas=3)

    assert not med_repo.ja_desbloqueada("sessao_medal1", "bronze")
    db.close()


def test_bronze_medal_unlocked_after_four_chapters():
    """
    Use case rule: Bronze requires caps 1-4 ALL complete.
    After completing all four chapters Bronze should be unlocked.
    """
    db = _fresh_db()
    med_repo = SQLMedalhaRepository(db)
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), med_repo)

    for cap in [1, 2, 3, 4]:
        use_case.execute("sessao_bronze4", capitulo_id=cap, acertos=3, total_perguntas=3)

    assert med_repo.ja_desbloqueada("sessao_bronze4", "Bronze")
    db.close()


def test_diamond_medal_not_unlocked_with_only_one_chapter():
    """Only one completed chapter should NOT unlock 'diamante'."""
    db = _fresh_db()
    med_repo = SQLMedalhaRepository(db)
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), med_repo)

    use_case.execute("sessao_medal2", capitulo_id=1, acertos=3, total_perguntas=3)

    assert not med_repo.ja_desbloqueada("sessao_medal2", "diamante")
    db.close()


def test_medal_not_duplicated_on_retry():
    """Completing the same chapter twice should NOT create duplicate medal records."""
    db = _fresh_db()
    med_repo = SQLMedalhaRepository(db)
    use_case = ResponderQuizUseCase(SQLProgressoRepository(db), med_repo)

    # Complete caps 1-4 to unlock bronze, then retry cap 1
    for cap in [1, 2, 3, 4]:
        use_case.execute("sessao_nodup", capitulo_id=cap, acertos=3, total_perguntas=3)
    use_case.execute("sessao_nodup", capitulo_id=1, acertos=3, total_perguntas=3)

    medalhas = med_repo.get_by_sessao("sessao_nodup")
    bronze_count = sum(1 for m in medalhas if m.medalha == "Bronze")
    assert bronze_count == 1
    db.close()


# ---------------------------------------------------------------------------
# Session isolation
# ---------------------------------------------------------------------------

def test_sessions_are_isolated():
    """Progress from one session must not affect another session."""
    db = _fresh_db()
    repo = SQLProgressoRepository(db)
    use_case = ResponderQuizUseCase(repo, SQLMedalhaRepository(db))

    use_case.execute("sessao_A", capitulo_id=1, acertos=3, total_perguntas=3)

    assert repo.get_by_sessao_e_capitulo("sessao_B", 1) is None
    db.close()
