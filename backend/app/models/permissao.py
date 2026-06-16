from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Permissao(Base):
    __tablename__ = "permissoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    codigo: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    nome: Mapped[str] = mapped_column(String(120), nullable=False)
    modulo: Mapped[str] = mapped_column(String(120), nullable=False)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )