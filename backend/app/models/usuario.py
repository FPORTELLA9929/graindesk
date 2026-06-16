from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    empresa: Mapped[str] = mapped_column(String(255), nullable=False)
    cnpj: Mapped[str] = mapped_column(String(20), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    telefone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    cargo: Mapped[str | None] = mapped_column(String(120), nullable=True)

    senha_hash: Mapped[str] = mapped_column(String(255), nullable=False)

    perfil: Mapped[str] = mapped_column(String(30), default="operacional", nullable=False)
    status: Mapped[str] = mapped_column(String(30), default="pendente", nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
    ultimo_login: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)