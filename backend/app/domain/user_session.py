from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class UserSession(Base):
    __tablename__ = "sessao_usuario"

    cod_sessao_usuario = Column(Integer, primary_key=True, index=True)
    identificador_sessao = Column(String(64), unique=True, nullable=False, index=True)
    cod_usuario = Column(Integer, ForeignKey("usuario.cod_usuario"), nullable=False, index=True)
    expira_em = Column(DateTime(timezone=False), nullable=False)
    ultimo_acesso_em = Column(DateTime(timezone=False), nullable=False)
    revogado_em = Column(DateTime(timezone=False), nullable=True)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
