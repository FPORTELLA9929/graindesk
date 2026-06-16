from datetime import datetime
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TipoVeiculo(Base):
    __tablename__ = "tipos_veiculo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    descricao: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )

    quantidade_eixos: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    quantidade_placas: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    capacidade_kg: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    capacidade_m3: Mapped[Decimal | None] = mapped_column(
        Numeric(12, 2),
        nullable=True,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )