"""
Concrete Repository implementations using SQLAlchemy.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from core.domain.entities import Progresso, Medalha
from core.application.repositories import AbstractProgressoRepository, AbstractMedalhaRepository
from core.infrastructure.database.models import ProgressoModel, MedalhaModel

class SQLProgressoRepository(AbstractProgressoRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_sessao(self, sessao_id: str) -> List[Progresso]:
        models = self.session.query(ProgressoModel).filter(ProgressoModel.sessao_id == sessao_id).all()
        return [
            Progresso(
                id=m.id, sessao_id=m.sessao_id, capitulo_id=m.capitulo_id,
                concluido=m.concluido, pontuacao=m.pontuacao, atualizado_em=m.atualizado_em
            ) for m in models
        ]

    def get_by_sessao_e_capitulo(self, sessao_id: str, capitulo_id: int) -> Optional[Progresso]:
        m = self.session.query(ProgressoModel).filter_by(sessao_id=sessao_id, capitulo_id=capitulo_id).first()
        if m:
            return Progresso(
                id=m.id, sessao_id=m.sessao_id, capitulo_id=m.capitulo_id,
                concluido=m.concluido, pontuacao=m.pontuacao, atualizado_em=m.atualizado_em
            )
        return None

    def salvar(self, progresso: Progresso) -> Progresso:
        if progresso.id:
            m = self.session.query(ProgressoModel).get(progresso.id)
            if m:
                m.concluido = progresso.concluido
                m.pontuacao = progresso.pontuacao
        else:
            m = ProgressoModel(
                sessao_id=progresso.sessao_id,
                capitulo_id=progresso.capitulo_id,
                concluido=progresso.concluido,
                pontuacao=progresso.pontuacao
            )
            self.session.add(m)
            
        self.session.commit()
        if not progresso.id:
            self.session.refresh(m)
            progresso.id = m.id
        return progresso

class SQLMedalhaRepository(AbstractMedalhaRepository):
    def __init__(self, session: Session):
        self.session = session

    def get_by_sessao(self, sessao_id: str) -> List[Medalha]:
        models = self.session.query(MedalhaModel).filter(MedalhaModel.sessao_id == sessao_id).all()
        return [
            Medalha(id=m.id, sessao_id=m.sessao_id, medalha=m.medalha, desbloqueada_em=m.desbloqueada_em)
            for m in models
        ]

    def desbloquear(self, medalha: Medalha) -> Medalha:
        m = MedalhaModel(sessao_id=medalha.sessao_id, medalha=medalha.medalha)
        self.session.add(m)
        self.session.commit()
        self.session.refresh(m)
        medalha.id = m.id
        medalha.desbloqueada_em = m.desbloqueada_em
        return medalha

    def ja_desbloqueada(self, sessao_id: str, medalha: str) -> bool:
        return self.session.query(MedalhaModel).filter_by(sessao_id=sessao_id, medalha=medalha).count() > 0
