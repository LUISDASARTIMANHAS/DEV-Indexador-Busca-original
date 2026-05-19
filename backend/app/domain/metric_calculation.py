from sqlalchemy import Column, DateTime, Integer, Numeric, func

from app.core.database import Base


class MetricCalculation(Base):
    __tablename__ = "calculo_metricas"

    cod_calculo_metricas = Column(Integer, primary_key=True, index=True)
    periodo_inicio = Column(DateTime(timezone=False), nullable=False)
    periodo_fim = Column(DateTime(timezone=False), nullable=False)
    total_consultas = Column(Integer, nullable=False, default=0)
    tempo_medio_respostas = Column(Numeric(19, 0), nullable=False, default=0)
    media_resultados = Column(Numeric(19, 0), nullable=False, default=0)
    consultas_sem_resultado = Column(Integer, nullable=False, default=0)
    calculado_em = Column(DateTime(timezone=False), server_default=func.now(), nullable=False)
