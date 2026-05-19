from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class DocumentAccessHistory(Base):
    __tablename__ = "acesso_documento"

    cod_acesso_documento = Column(Integer, primary_key=True, index=True)
    cod_documento = Column(Integer, ForeignKey("documento.cod_documento"), nullable=False, index=True)
    cod_usuario = Column(Integer, ForeignKey("usuario.cod_usuario"), nullable=False, index=True)
    tipo_acesso = Column(String(20), nullable=False)
    origem = Column(String(80), nullable=True)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
