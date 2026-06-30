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


class Ciot(Base):
    __tablename__ = "ciots"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(Integer, ForeignKey("empresas.id"), nullable=False, index=True)
    transportador_id = Column(Integer, ForeignKey("transportadores.id"), nullable=False, index=True)
    motorista_id = Column(Integer, ForeignKey("motoristas.id"), nullable=False, index=True)
    veiculo_id = Column(Integer, ForeignKey("veiculos.id"), nullable=False, index=True)
    rota_id = Column(Integer, ForeignKey("rotas.id"), nullable=False, index=True)

    mdfe_id = Column(Integer, ForeignKey("mdfes.id"), nullable=True, index=True)

    numero_ciot = Column(String(50), nullable=True, index=True)
    protocolo = Column(String(100), nullable=True)

    status = Column(String(30), nullable=False, default="rascunho")

    tipo_emissao = Column(String(20), nullable=False, default="antt")
    ambiente = Column(String(20), nullable=False, default="homologacao")

    valor_frete = Column(Numeric(15, 2), nullable=True)
    forma_pagamento = Column(String(30), nullable=False, default="transferencia_bancaria")
    responsavel_pagamento_cnpj = Column(String(14), nullable=True)

    data_inicio = Column(DateTime(timezone=True), nullable=True)
    data_fim = Column(DateTime(timezone=True), nullable=True)

    payload_enviado = Column(Text, nullable=True)
    retorno_api = Column(Text, nullable=True)
    mensagem_retorno = Column(Text, nullable=True)

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
    mdfe = relationship("Mdfe", backref="ciots")

    def __repr__(self):
        return (
            f"<Ciot("
            f"id={self.id}, "
            f"numero_ciot='{self.numero_ciot}', "
            f"status='{self.status}', "
            f"mdfe_id={self.mdfe_id}"
            f")>"
        )