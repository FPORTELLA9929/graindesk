from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PortalUnicoConsultaCCTItem(Base):
    __tablename__ = "portal_unico_consulta_cct_itens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    consulta_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("portal_unico_consultas_cct.id"),
        nullable=False,
        index=True,
    )

    chave: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
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

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    consulta = relationship(
        "PortalUnicoConsultaCCT",
        back_populates="itens",
    )