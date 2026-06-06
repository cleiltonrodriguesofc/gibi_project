"""SQLAlchemy ORM models. Maps to core.domain.entities"""
from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass

class ProgressoModel(Base):
    __tablename__ = "progresso"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(String, index=True, nullable=False)
    capitulo_id = Column(Integer, nullable=False)
    concluido = Column(Boolean, default=False)
    pontuacao = Column(Integer, default=0)
    atualizado_em = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class MedalhaModel(Base):
    __tablename__ = "medalhas"

    id = Column(Integer, primary_key=True, index=True)
    sessao_id = Column(String, index=True, nullable=False)
    medalha = Column(String, nullable=False)
    desbloqueada_em = Column(DateTime, default=datetime.utcnow)
