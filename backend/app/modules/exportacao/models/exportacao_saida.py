from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class ExportacaoSaida(Base):
    __tablename__ = "exportacao_saidas"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
        index=True,
    )

    chave_nfe = Column(
        String(44),
        nullable=False,
        unique=True,
        index=True,
    )

    numero_nfe = Column(
        String(20),
        nullable=True,
        index=True,
    )

    serie = Column(
        String(10),
        nullable=True,
    )

    destinatario_nome = Column(
        String(255),
        nullable=True,
    )

    destinatario_documento = Column(
        String(20),
        nullable=True,
    )

    data_emissao = Column(
        DateTime,
        nullable=True,
    )

    cfop = Column(
        String(10),
        nullable=True,
        index=True,
    )

    ncm = Column(
        String(20),
        nullable=True,
        index=True,
    )

    produto = Column(
        String(255),
        nullable=True,
    )

    quantidade_exportada = Column(
        Numeric(15, 4),
        nullable=False,
        default=0,
    )

    valor_exportado = Column(
        Numeric(15, 2),
        nullable=False,
        default=0,
    )

    status = Column(
        String(20),
        nullable=False,
        default="processada",
        index=True,
    )

    observacoes = Column(
        Text,
        nullable=True,
    )

    xml_path = Column(
        String(500),
        nullable=True,
    )

    criado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    atualizado_em = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    empresa = relationship(
        "Empresa",
    )

    consumos = relationship(
        "ExportacaoConsumo",
        back_populates="saida",
        cascade="all, delete-orphan",
    )

    itens_exportacao = relationship(
        "ExportacaoSaidaItem",
        back_populates="saida",
        cascade="all, delete-orphan",
    )