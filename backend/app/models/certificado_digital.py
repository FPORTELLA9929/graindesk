from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.database.base import Base


class CertificadoDigital(Base):
    __tablename__ = "certificados_digitais"

    id = Column(Integer, primary_key=True, index=True)

    empresa_id = Column(
        Integer,
        ForeignKey("empresas.id"),
        nullable=False,
        index=True,
    )

    cnpj_certificado = Column(
        String(14),
        nullable=False,
        index=True,
    )

    cnpj_raiz = Column(
        String(8),
        nullable=False,
        index=True,
    )

    razao_social_certificado = Column(
        String(255),
        nullable=True,
    )

    serial_number = Column(
        String(255),
        nullable=True,
    )

    emissor = Column(
        String(255),
        nullable=True,
    )

    data_emissao = Column(
        Date,
        nullable=True,
    )

    data_validade = Column(
        Date,
        nullable=True,
    )

    arquivo_path = Column(
        String(500),
        nullable=False,
    )

    senha_criptografada = Column(
        String(1000),
        nullable=False,
    )

    tipo_certificado = Column(
        String(10),
        nullable=False,
        default="A1",
    )

    ativo = Column(
        Boolean,
        nullable=False,
        default=True,
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
        backref="certificados_digitais",
    )

    @property
    def dias_para_vencimento(self):
        if not self.data_validade:
            return None

        from datetime import date

        return (self.data_validade - date.today()).days

    @property
    def vencido(self):
        dias = self.dias_para_vencimento

        if dias is None:
            return False

        return dias < 0

    def __repr__(self):
        return (
            f"<CertificadoDigital("
            f"id={self.id}, "
            f"cnpj={self.cnpj_certificado}, "
            f"validade={self.data_validade}, "
            f"ativo={self.ativo}"
            f")>"
        )