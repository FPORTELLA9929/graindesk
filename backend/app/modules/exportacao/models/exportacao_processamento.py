from sqlalchemy import (
    Column,
    DateTime,
    Integer,
    String,
    Text,
)
from sqlalchemy.sql import func

from app.database.base import Base


class ExportacaoProcessamento(Base):
    __tablename__ = "exportacao_processamentos"

    id = Column(Integer, primary_key=True, index=True)

    tipo = Column(
        String(50),
        nullable=False,
        index=True,
    )

    status = Column(
        String(20),
        nullable=False,
        default="pendente",
        index=True,
    )

    usuario_id = Column(
        Integer,
        nullable=True,
        index=True,
    )

    entradas_processadas = Column(
        Integer,
        nullable=False,
        default=0,
    )

    saidas_processadas = Column(
        Integer,
        nullable=False,
        default=0,
    )

    itens_processados = Column(
        Integer,
        nullable=False,
        default=0,
    )

    consumos_gerados = Column(
        Integer,
        nullable=False,
        default=0,
    )

    mensagem = Column(Text, nullable=True)
    erro = Column(Text, nullable=True)

    iniciado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    finalizado_em = Column(
        DateTime(timezone=True),
        nullable=True,
    )