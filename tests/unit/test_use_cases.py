from core.application.use_cases import ResponderQuizUseCase
from core.infrastructure.database.repositories import SQLProgressoRepository, SQLMedalhaRepository
from core.infrastructure.database.models import Base
from tests.conftest import TestingSessionLocal, engine

def test_responder_quiz_sucesso():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    
    prog_repo = SQLProgressoRepository(db)
    med_repo = SQLMedalhaRepository(db)
    use_case = ResponderQuizUseCase(prog_repo, med_repo)
    
    # Simulate correct answers (3 out of 3)
    result = use_case.execute("sessao_123", 1, 3, 3)
    
    assert result["sucesso"] is True
    assert result["acertos"] == 3
    
    progresso = prog_repo.get_by_sessao_e_capitulo("sessao_123", 1)
    assert progresso is not None
    assert progresso.concluido is True
    
    db.close()
