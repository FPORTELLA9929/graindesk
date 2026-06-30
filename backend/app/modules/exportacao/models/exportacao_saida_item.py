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


class ExportacaoSaidaItem(Base):
    __tablename__ = "exportacao_saida_itens"

    id = Column(Integer, primary_key=True, index=True)

    saida_id = Column(
        Integer,
        ForeignKey("exportacao_saidas.id"),
        nullable=False,
        index=True,
    )

    chave_nfe_saida = Column(String(44), nullable=False, index=True)
    numero_nfe_saida = Column(String(20), nullable=True, index=True)

    chave_nfe_entrada = Column(String(44), nullable=False, index=True)
    numero_re = Column(String(20), nullable=True, index=True)

    quantidade_consumida = Column(
        Numeric(15, 4),
        nullable=False,
        default=0,
    )

    criado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    saida = relationship(
        "ExportacaoSaida",
        back_populates="itens_exportacao",
    )