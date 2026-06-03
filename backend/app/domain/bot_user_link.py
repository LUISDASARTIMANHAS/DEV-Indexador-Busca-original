from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint, func

from app.core.database import Base


class BotUserLink(Base):
    __tablename__ = "bot_usuario_vinculado"
    __table_args__ = (
        UniqueConstraint("canal", "usuario_externo", name="uq_bot_vinculo_canal_usuario"),
    )

    cod_vinculo = Column(Integer, primary_key=True, index=True)
    cod_usuario = Column(Integer, ForeignKey("usuario.cod_usuario"), nullable=False)
    canal = Column(String(50), nullable=False, index=True)
    usuario_externo = Column(String(255), nullable=False, index=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
