from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PortalUnicoURF(Base):
    __tablename__ = "portal_unico_urfs"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    codigo: Mapped[str] = mapped_column(
        String(20),
        unique=True,
        index=True,
        nullable=False,
    )

    descricao: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    ativo: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        nullable=False,
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        server_default=func.now(),
        onupdate=datetime.utcnow,
        nullable=False,
    )