from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ExportacaoConsumo(Base):
    __tablename__ = "exportacao_consumos"

    id = Column(Integer, primary_key=True, index=True)

    entrada_id = Column(
        Integer,
        ForeignKey("exportacao_entradas.id"),
        nullable=False,
        index=True,
    )

    saida_id = Column(
        Integer,
        ForeignKey("exportacao_saidas.id"),
        nullable=False,
        index=True,
    )

    chave_nfe_entrada = Column(String(44), nullable=False, index=True)
    chave_nfe_saida = Column(String(44), nullable=False, index=True)

    numero_nfe_entrada = Column(String(20), nullable=True, index=True)
    numero_nfe_saida = Column(String(20), nullable=True, index=True)

    numero_re = Column(String(20), nullable=True, index=True)

    quantidade_consumida = Column(Numeric(15, 4), nullable=False, default=0)

    criado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    entrada = relationship(
        "ExportacaoEntrada",
        back_populates="consumos",
    )

    saida = relationship(
        "ExportacaoSaida",
        back_populates="consumos",
    )