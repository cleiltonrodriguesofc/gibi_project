"""
Use Cases (Interactors) orchestrate the domain logic and coordinate with repositories.
"""
from typing import List
from core.domain.entities import Progresso, Medalha
from core.application.repositories import AbstractProgressoRepository, AbstractMedalhaRepository

class ResponderQuizUseCase:
    """Handles the business logic when a user answers a quiz question."""

    def __init__(self, progresso_repo: AbstractProgressoRepository, medalhas_repo: AbstractMedalhaRepository):
        self.progresso_repo = progresso_repo
        self.medalhas_repo = medalhas_repo

    def execute(self, sessao_id: str, capitulo_id: int, acertos: int, total_perguntas: int) -> dict:
        # Check if completed successfully (e.g., 2 or more out of 3)
        concluido = acertos >= 2

        progresso = self.progresso_repo.get_by_sessao_e_capitulo(sessao_id, capitulo_id)
        if not progresso:
            progresso = Progresso(
                sessao_id=sessao_id,
                capitulo_id=capitulo_id,
                concluido=concluido,
                pontuacao=acertos
            )
        else:
            progresso.concluido = concluido or progresso.concluido
            progresso.pontuacao = max(progresso.pontuacao, acertos)

        self.progresso_repo.salvar(progresso)
        
        # Check for medals based on completion logic
        self._check_and_unlock_medals(sessao_id)

        return {"sucesso": concluido, "acertos": acertos, "progresso_salvo": True}

    def _check_and_unlock_medals(self, sessao_id: str):
        # Implementation of gamification logic based on completed chapters
        progressos = self.progresso_repo.get_by_sessao(sessao_id)
        concluidos = {p.capitulo_id for p in progressos if p.concluido}

        # Medalha Bronze (Cap 1 a 4)
        if {1, 2, 3, 4}.issubset(concluidos) and not self.medalhas_repo.ja_desbloqueada(sessao_id, "Bronze"):
            self.medalhas_repo.desbloquear(Medalha(sessao_id=sessao_id, medalha="Bronze"))

        # Medalha Prata (Cap 5 a 9)
        if {5, 6, 7, 8, 9}.issubset(concluidos) and not self.medalhas_repo.ja_desbloqueada(sessao_id, "Prata"):
            self.medalhas_repo.desbloquear(Medalha(sessao_id=sessao_id, medalha="Prata"))

        # Medalha Ouro (Cap 10 a 14)
        if {10, 11, 12, 13, 14}.issubset(concluidos) and not self.medalhas_repo.ja_desbloqueada(sessao_id, "Ouro"):
            self.medalhas_repo.desbloquear(Medalha(sessao_id=sessao_id, medalha="Ouro"))

        # Diamante (1 a 16)
        if set(range(1, 17)).issubset(concluidos) and not self.medalhas_repo.ja_desbloqueada(sessao_id, "Diamante"):
            self.medalhas_repo.desbloquear(Medalha(sessao_id=sessao_id, medalha="Diamante"))
