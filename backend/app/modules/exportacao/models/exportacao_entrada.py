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


class ExportacaoEntrada(Base):
    __tablename__ = "exportacao_entradas"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    chave_nfe = Column(String(44), nullable=False, unique=True, index=True)
    numero_nfe = Column(String(20), nullable=True, index=True)
    serie = Column(String(10), nullable=True)

    fornecedor_nome = Column(String(255), nullable=True)
    fornecedor_cnpj = Column(String(14), nullable=True, index=True)

    data_emissao = Column(DateTime, nullable=True)

    prazo_legal_dias = Column(Integer, nullable=False, default=180)
    data_limite_exportacao = Column(DateTime, nullable=True, index=True)

    situacao_prazo = Column(String(20), nullable=False, default="normal", index=True)

    cfop = Column(String(10), nullable=True, index=True)
    ncm = Column(String(20), nullable=True, index=True)
    produto = Column(String(255), nullable=True)

    quantidade_original = Column(Numeric(15, 4), nullable=False, default=0)
    quantidade_saldo = Column(Numeric(15, 4), nullable=False, default=0)

    valor_original = Column(Numeric(15, 2), nullable=False, default=0)

    status = Column(String(20), nullable=False, default="disponivel", index=True)

    observacoes = Column(Text, nullable=True)
    xml_path = Column(String(500), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    empresa = relationship("Empresa")

    consumos = relationship(
        "ExportacaoConsumo",
        back_populates="entrada",
        cascade="all, delete-orphan",
    )

    reservas_itens = relationship(
        "ExportacaoEntradaReservaItem",
        back_populates="entrada",
        cascade="all, delete-orphan",
    )


class ExportacaoEntradaReserva(Base):
    __tablename__ = "exportacao_entrada_reservas"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)

    produto = Column(String(255), nullable=True, index=True)
    ncm = Column(String(20), nullable=True, index=True)

    quantidade_solicitada = Column(Numeric(15, 4), nullable=False, default=0)
    quantidade_reservada = Column(Numeric(15, 4), nullable=False, default=0)
    quantidade_consumida = Column(Numeric(15, 4), nullable=False, default=0)

    status = Column(String(20), nullable=False, default="ativa", index=True)

    observacoes = Column(Text, nullable=True)

    criado_por = Column(String(255), nullable=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    empresa = relationship("Empresa")

    itens = relationship(
        "ExportacaoEntradaReservaItem",
        back_populates="reserva",
        cascade="all, delete-orphan",
    )


class ExportacaoEntradaReservaItem(Base):
    __tablename__ = "exportacao_entrada_reserva_itens"

    id = Column(Integer, primary_key=True, index=True)

    reserva_id = Column(
        Integer,
        ForeignKey("exportacao_entrada_reservas.id"),
        nullable=False,
        index=True,
    )

    entrada_id = Column(
        Integer,
        ForeignKey("exportacao_entradas.id"),
        nullable=False,
        index=True,
    )

    chave_nfe = Column(String(44), nullable=False, index=True)
    numero_nfe = Column(String(20), nullable=True)

    quantidade_reservada = Column(Numeric(15, 4), nullable=False, default=0)
    quantidade_consumida = Column(Numeric(15, 4), nullable=False, default=0)

    status = Column(String(20), nullable=False, default="ativa", index=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    reserva = relationship("ExportacaoEntradaReserva", back_populates="itens")
    entrada = relationship("ExportacaoEntrada", back_populates="reservas_itens")