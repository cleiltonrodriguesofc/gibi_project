"""
Pure domain entities — no external dependencies allowed here.
These are plain dataclasses representing the core business concepts.
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Capitulo:
    """Represents a comic book chapter with its educational content."""
    id: int
    titulo: str
    descricao: str
    disponivel: bool
    animacao: str  # filename in /static/animations/
    quadros: list  # list of panel dicts {imagem, texto, personagem}
    explicacao: str
    conquista_nome: str
    conquista_icone: str


@dataclass
class QuizPergunta:
    """A multiple-choice quiz question for a chapter."""
    id: int
    capitulo_id: int
    pergunta: str
    opcoes: list  # ["option A", "option B", "option C", "option D"]
    resposta_correta: int  # index of correct option (0-based)


@dataclass
class Progresso:
    """Tracks reading and quiz progress for an anonymous session."""
    id: Optional[int] = None
    sessao_id: str = ""
    capitulo_id: int = 0
    concluido: bool = False
    pontuacao: int = 0
    atualizado_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class Medalha:
    """A gamification badge unlocked by completing a set of chapters."""
    id: Optional[int] = None
    sessao_id: str = ""
    medalha: str = ""  # bronze | prata | ouro | diamante
    desbloqueada_em: datetime = field(default_factory=datetime.utcnow)


@dataclass
class UnidadeSaude:
    """A health unit shown on the geolocation map."""
    nome: str
    endereco: str
    telefone: str
    tipo: str  # UBS | UPA | Hospital
    lat: float
    lng: float
