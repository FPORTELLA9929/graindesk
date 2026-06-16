from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Transportador(Base):
    __tablename__ = "transportadores"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    tipo_pessoa: Mapped[str] = mapped_column(String(2), nullable=False)

    nome_razao_social: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    nome_fantasia: Mapped[str | None] = mapped_column(String(255), nullable=True)

    cpf_cnpj: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    rg_ie: Mapped[str | None] = mapped_column(String(30), nullable=True)

    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)

    municipio_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("municipios.codigo_ibge"),
        nullable=False,
        index=True,
    )

    endereco: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )