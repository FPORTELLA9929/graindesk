from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class Mdfe(Base):
    __tablename__ = "mdfes"

    id = Column(Integer, primary_key=True, index=True)

    numero = Column(
        Integer,
        nullable=False,
        default=1,
    )

    serie = Column(
        Integer,
        nullable=False,
        default=1,
    )

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
    )

    transportador_id = Column(
        Integer,
        ForeignKey("transportadores.id"),
        nullable=False,
    )

    motorista_id = Column(
        Integer,
        ForeignKey("motoristas.id"),
        nullable=False,
    )

    veiculo_id = Column(
        Integer,
        ForeignKey("veiculos.id"),
        nullable=False,
    )

    rota_id = Column(
        Integer,
        ForeignKey("rotas.id"),
        nullable=False,
    )

    uf_inicio = Column(
        String(2),
        nullable=False,
    )

    uf_fim = Column(
        String(2),
        nullable=False,
    )

    status = Column(
        String(20),
        nullable=False,
        default="rascunho",
    )

    observacoes = Column(
        Text,
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

    empresa = relationship("Empresa")
    transportador = relationship("Transportador")
    motorista = relationship("Motorista")
    veiculo = relationship("Veiculo")
    rota = relationship("Rota")

    def __repr__(self):
        return (
            f"<Mdfe("
            f"id={self.id}, "
            f"numero={self.numero}, "
            f"status='{self.status}'"
            f")>"
        )