from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String, UniqueConstraint, func

from app.core.database import Base


class DocumentEmbedding(Base):
    __tablename__ = "documento_embedding"
    __table_args__ = (
        UniqueConstraint(
            "cod_documento",
            "versao_documento",
            "modelo_embedding",
            name="uq_documento_embedding_documento_versao_modelo",
        ),
    )

    cod_embedding = Column(Integer, primary_key=True, index=True)
    cod_documento = Column(Integer, ForeignKey("documento.cod_documento"), nullable=False)
    versao_documento = Column(Integer, nullable=True)
    modelo_embedding = Column(String(255), nullable=False)
    embedding = Column(JSON, nullable=False)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
