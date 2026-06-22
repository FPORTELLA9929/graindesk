from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class TransportadorDadoBancario(Base):
    __tablename__ = "transportador_dados_bancarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    transportador_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("transportadores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    banco_codigo: Mapped[str | None] = mapped_column(String(10), nullable=True)
    banco_nome: Mapped[str | None] = mapped_column(String(100), nullable=True)

    agencia: Mapped[str | None] = mapped_column(String(20), nullable=True)
    conta: Mapped[str | None] = mapped_column(String(30), nullable=True)
    digito_conta: Mapped[str | None] = mapped_column(String(10), nullable=True)

    tipo_conta: Mapped[str | None] = mapped_column(String(20), nullable=True)

    favorecido: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cpf_cnpj_favorecido: Mapped[str | None] = mapped_column(String(20), nullable=True)

    tipo_pix: Mapped[str | None] = mapped_column(String(20), nullable=True)
    chave_pix: Mapped[str | None] = mapped_column(String(255), nullable=True)

    principal: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    ativo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    criado_em: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    atualizado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )