from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Integer,
    String,
)
from sqlalchemy.sql import func

from app.database.base import Base


class ConfiguracaoFiscal(Base):
    __tablename__ = "configuracoes_fiscais"

    id = Column(Integer, primary_key=True, index=True)

    ambiente = Column(
        String(20),
        nullable=False,
        default="homologacao",
    )

    uf_emitente = Column(
        String(2),
        nullable=False,
        default="PR",
    )

    versao_mdfe = Column(
        String(10),
        nullable=False,
        default="3.00",
    )

    versao_nfe = Column(
        String(10),
        nullable=False,
        default="4.00",
    )

    timeout_sefaz = Column(
        Integer,
        nullable=False,
        default=30,
    )

    tentativas_envio = Column(
        Integer,
        nullable=False,
        default=3,
    )

    contingencia_automatica = Column(
        Boolean,
        nullable=False,
        default=False,
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

    def __repr__(self):
        return (
            f"<ConfiguracaoFiscal("
            f"id={self.id}, "
            f"ambiente={self.ambiente}, "
            f"uf={self.uf_emitente}, "
            f"ativo={self.ativo}"
            f")>"
        )