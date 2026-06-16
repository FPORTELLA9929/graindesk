from sqlalchemy import Boolean, Column, DateTime, Integer, String, func

from app.database.base import Base


class Fornecedor(Base):
    __tablename__ = "fornecedores"

    id = Column(Integer, primary_key=True, index=True)

    razao_social = Column(String(255), nullable=False)
    nome_fantasia = Column(String(255), nullable=True)

    cpf_cnpj = Column(String(20), nullable=False, unique=True, index=True)
    inscricao_estadual = Column(String(50), nullable=True)

    telefone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)

    logradouro = Column(String(255), nullable=True)
    numero = Column(String(50), nullable=True)
    bairro = Column(String(150), nullable=True)
    cidade = Column(String(150), nullable=True)
    estado = Column(String(2), nullable=True)
    cep = Column(String(20), nullable=True)

    ativo = Column(Boolean, nullable=False, default=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())