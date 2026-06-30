from datetime import datetime

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class PortalUnicoConsultaCCT(Base):
    __tablename__ = "portal_unico_consultas_cct"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    usuario_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
    usuario_nome: Mapped[str | None] = mapped_column(String(255), nullable=True)

    status: Mapped[str] = mapped_column(String(30), nullable=False, default="pendente", index=True)

    quantidade_chaves: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantidade_ok: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantidade_invalidas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    quantidade_nao_encontradas: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    mensagem: Mapped[str | None] = mapped_column(Text, nullable=True)
    erro: Mapped[str | None] = mapped_column(Text, nullable=True)

    iniciado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finalizado_em: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

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

    itens = relationship(
        "PortalUnicoConsultaCCTItem",
        back_populates="consulta",
        cascade="all, delete-orphan",
    )