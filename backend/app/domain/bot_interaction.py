from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, func
from sqlalchemy.types import JSON

from app.core.database import Base


class BotInteraction(Base):
    __tablename__ = "bot_interacao"

    cod_interacao = Column(Integer, primary_key=True, index=True)
    canal = Column(String(50), nullable=False, index=True)
    usuario_externo = Column(String(255), nullable=False, index=True)
    mensagem_usuario = Column(Text, nullable=False)
    intencao_detectada = Column(String(100), nullable=True)
    entidades = Column(JSON, nullable=True)
    resposta_bot = Column(Text, nullable=True)
    sucesso = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
