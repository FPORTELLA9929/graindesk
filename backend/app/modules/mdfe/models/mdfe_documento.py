from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MdfeDocumento(Base):
    __tablename__ = "mdfe_documentos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    mdfe_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("mdfes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    chave_nfe: Mapped[str] = mapped_column(String(44), nullable=False, index=True)
    numero_nfe: Mapped[str | None] = mapped_column(String(20), nullable=True)

    produto: Mapped[str | None] = mapped_column(String(255), nullable=True)
    ncm: Mapped[str | None] = mapped_column(String(8), nullable=True)

    quantidade: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    peso_bruto: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    peso_liquido: Mapped[Decimal | None] = mapped_column(Numeric(15, 4), nullable=True)
    valor_carga: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    tarifa_rota: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    pedagio_por_eixo: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    frete_base: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    pedagio_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)
    frete_total: Mapped[Decimal | None] = mapped_column(Numeric(15, 2), nullable=True)

    xml_path: Mapped[str | None] = mapped_column(String(500), nullable=True)

    observacao: Mapped[str | None] = mapped_column(Text, nullable=True)

    criado_em: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )

    mdfe = relationship("Mdfe", backref="documentos")

    def __repr__(self):
        return (
            f"<MdfeDocumento("
            f"id={self.id}, "
            f"mdfe_id={self.mdfe_id}, "
            f"chave_nfe='{self.chave_nfe}'"
            f")>"
        )