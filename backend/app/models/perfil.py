from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Perfil(Base):
    __tablename__ = "perfis"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    nome: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    descricao: Mapped[str | None] = mapped_column(String(255), nullable=True)

    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )