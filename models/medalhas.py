"""SQLAlchemy model for gamification badges (medalhas)."""
from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from models import Base


class Medalha(Base):
    """Stores unlocked badges for each anonymous session."""

    __tablename__ = "medalhas"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(String, index=True, nullable=False)
    medalha = Column(String, nullable=False)  # bronze | prata | ouro | diamante
    desbloqueada_em = Column(DateTime, default=datetime.utcnow)
