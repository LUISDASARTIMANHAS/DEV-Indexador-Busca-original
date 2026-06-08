from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func

from app.core.database import Base


class OCRHistory(Base):
    __tablename__ = "historico_ocr"

    cod_ocr = Column(Integer, primary_key=True, index=True)
    cod_documento = Column(Integer, ForeignKey("documento.cod_documento"), nullable=False, index=True)
    cod_historico_documento = Column(
        Integer,
        ForeignKey("historico_documento.cod_historico_documento"),
        nullable=True,
        index=True,
    )
    status = Column(String(50), nullable=False)
    idioma = Column(String(20), nullable=True)
    paginas_processadas = Column(Integer, nullable=True)
    tamanho_texto = Column(Integer, nullable=True)
    tempo_ms = Column(Integer, nullable=True)
    erro = Column(Text, nullable=True)
    executado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
