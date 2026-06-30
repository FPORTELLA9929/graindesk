from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PortalUnicoCCTSaldo(Base):
    __tablename__ = "portal_unico_cct_saldos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    chave: Mapped[str] = mapped_column(
        String(44),
        nullable=False,
        unique=True,
        index=True,
    )

    numero_nfe: Mapped[str | None] = mapped_column(String(20), nullable=True, index=True)
    centro_origem: Mapped[str | None] = mapped_column(String(255), nullable=True)
    material: Mapped[str | None] = mapped_column(String(255), nullable=True)

    peso_nf: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    peso_cct: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)
    saldo: Mapped[Decimal] = mapped_column(Numeric(15, 4), nullable=False, default=0)

    porto: Mapped[str | None] = mapped_column(String(255), nullable=True)
    recinto: Mapped[str | None] = mapped_column(String(255), nullable=True)

    situacao: Mapped[str | None] = mapped_column(String(50), nullable=True, index=True)
    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)

    json_retorno: Mapped[dict | None] = mapped_column(JSONB, nullable=True)

    primeira_consulta_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    ultima_consulta_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )