from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ExportacaoRE(Base):
    __tablename__ = "exportacao_res"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
        index=True,
    )

    numero_re = Column(
        String(20),
        nullable=False,
        index=True,
    )

    numero_due = Column(
        String(30),
        nullable=True,
        index=True,
    )

    quantidade_total = Column(
        Numeric(15, 4),
        nullable=False,
        default=0,
    )

    quantidade_consumida = Column(
        Numeric(15, 4),
        nullable=False,
        default=0,
    )

    status = Column(
        String(20),
        nullable=False,
        default="aberto",
        index=True,
    )

    observacoes = Column(Text, nullable=True)

    criado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    empresa = relationship("Empresa")