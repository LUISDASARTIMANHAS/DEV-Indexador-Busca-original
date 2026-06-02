from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, Numeric, String, Text, func

from app.core.database import Base


class DocumentHistory(Base):
    __tablename__ = "historico_documento"

    cod_historico_documento = Column(Integer, primary_key=True, index=True)
    cod_documento = Column(Integer, ForeignKey("documento.cod_documento"), nullable=False)
    cod_usuario = Column(Integer, ForeignKey("usuario.cod_usuario"), nullable=False)
    numero_versao = Column(Numeric(19, 0), nullable=False)
    caminho_arquivo = Column(String(255), nullable=False)
    nome_arquivo_original = Column(String(255), nullable=True)
    mime_type = Column(String(255), nullable=True)
    tamanho_bytes = Column(Integer, nullable=True)
    hash_arquivo = Column(String(64), nullable=True)
    texto_extraido = Column(Text, nullable=True)
    texto_processado = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
    versao_ativa = Column(Boolean, default=False, nullable=False)
