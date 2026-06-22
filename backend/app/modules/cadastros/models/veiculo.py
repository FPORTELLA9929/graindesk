from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Veiculo(Base):
    __tablename__ = "veiculos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transportador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transportadores.id"),
        nullable=False,
        index=True,
    )

    tipo_veiculo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("tipos_veiculo.id"),
        nullable=False,
        index=True,
    )

    observacao: Mapped[str | None] = mapped_column(
        String(500),
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


class VeiculoPlaca(Base):
    __tablename__ = "veiculo_placas"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    veiculo_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("veiculos.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    descricao: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    placa: Mapped[str] = mapped_column(
        String(10),
        nullable=False,
        index=True,
    )

    renavam: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    tara_kg: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    capacidade_kg: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    capacidade_m3: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    cpf_cnpj_proprietario: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    rntrc: Mapped[str | None] = mapped_column(
        String(30),
        nullable=True,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )