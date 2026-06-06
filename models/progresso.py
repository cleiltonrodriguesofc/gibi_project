"""SQLAlchemy models for tracking reading progress per anonymous session."""
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Integer, String

from models import Base


class Progresso(Base):
    """Stores chapter completion and quiz score for each anonymous session."""

    __tablename__ = "progresso"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(String, index=True, nullable=False)
    capitulo_id = Column(Integer, nullable=False)
    concluido = Column(Boolean, default=False)
    pontuacao = Column(Integer, default=0)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
