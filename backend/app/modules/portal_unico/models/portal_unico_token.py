from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PortalUnicoToken(Base):
    __tablename__ = "portal_unico_tokens"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    token: Mapped[str] = mapped_column(Text, nullable=False)
    csrf_token: Mapped[str | None] = mapped_column(Text, nullable=True)

    role_type: Mapped[str] = mapped_column(String(30), nullable=False, default="IMPEXP")
    ambiente: Mapped[str] = mapped_column(String(30), nullable=False, default="producao")

    gerado_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    expira_em: Mapped[datetime] = mapped_column(DateTime, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )

    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )