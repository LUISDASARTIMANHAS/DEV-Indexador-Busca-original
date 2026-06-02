from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func

from app.core.database import Base


class RelevanceFeedback(Base):
    __tablename__ = "feedback_relevancia"

    cod_feedback_relevancia = Column(Integer, primary_key=True, index=True)
    cod_usuario = Column(Integer, ForeignKey("usuario.cod_usuario"), nullable=False)
    cod_historico_busca = Column(Integer, ForeignKey("historico_busca.cod_historico_busca"), nullable=False)
    cod_documento = Column(Integer, ForeignKey("documento.cod_documento"), nullable=False)
    nota = Column(Integer, nullable=True)
    comentario = Column(String(255), nullable=True)
    criado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
