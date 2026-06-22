from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Integer, Numeric, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Rota(Base):
    __tablename__ = "rotas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    municipio_origem_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("municipios.codigo_ibge"),
        nullable=False,
        index=True,
    )

    municipio_destino_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("municipios.codigo_ibge"),
        nullable=False,
        index=True,
    )

    distancia_km: Mapped[Decimal | None] = mapped_column(Numeric(10, 2), nullable=True)
    tarifa: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    possui_pedagio: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    valor_pedagio_por_eixo: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), nullable=True)

    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    vigencia_inicio: Mapped[date | None] = mapped_column(Date, nullable=True)
    vigencia_fim: Mapped[date | None] = mapped_column(Date, nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )