"""
Abstract repository interfaces for the application layer.
Concrete implementations live in core/infrastructure/database/repositories.py.
"""
from abc import ABC, abstractmethod
from typing import List, Optional

from core.domain.entities import Medalha, Progresso


class AbstractProgressoRepository(ABC):
    """Interface for persisting and querying chapter progress."""

    @abstractmethod
    def get_by_sessao(self, sessao_id: str) -> List[Progresso]:
        """Return all progress records for the given session."""
        ...

    @abstractmethod
    def get_by_sessao_e_capitulo(self, sessao_id: str, capitulo_id: int) -> Optional[Progresso]:
        """Return progress for a specific chapter and session."""
        ...

    @abstractmethod
    def salvar(self, progresso: Progresso) -> Progresso:
        """Insert or update a progress record."""
        ...


class AbstractMedalhaRepository(ABC):
    """Interface for persisting and querying unlocked badges."""

    @abstractmethod
    def get_by_sessao(self, sessao_id: str) -> List[Medalha]:
        """Return all medals unlocked for the given session."""
        ...

    @abstractmethod
    def desbloquear(self, medalha: Medalha) -> Medalha:
        """Persist a newly unlocked medal."""
        ...

    @abstractmethod
    def ja_desbloqueada(self, sessao_id: str, medalha: str) -> bool:
        """Check if a specific medal was already unlocked for this session."""
        ...
