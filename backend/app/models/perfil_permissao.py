from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class PerfilPermissao(Base):
    __tablename__ = "perfil_permissoes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    perfil_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("perfis.id", ondelete="CASCADE"),
        nullable=False,
    )

    permissao_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("permissoes.id", ondelete="CASCADE"),
        nullable=False,
    )

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )