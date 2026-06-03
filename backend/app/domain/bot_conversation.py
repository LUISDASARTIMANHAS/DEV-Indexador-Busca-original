from sqlalchemy import Column, DateTime, Integer, String, UniqueConstraint, func
from sqlalchemy.types import JSON

from app.core.database import Base


class BotConversation(Base):
    __tablename__ = "bot_conversa"
    __table_args__ = (
        UniqueConstraint("canal", "usuario_externo", name="uq_bot_conversa_canal_usuario"),
    )

    cod_conversa = Column(Integer, primary_key=True, index=True)
    canal = Column(String(50), nullable=False, index=True)
    usuario_externo = Column(String(255), nullable=False, index=True)
    ultima_intencao = Column(String(100), nullable=True)
    ultimo_contexto = Column(JSON, nullable=True)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=False), server_default=func.now(), onupdate=func.now(), nullable=False)
