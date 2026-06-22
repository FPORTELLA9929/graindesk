from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.database.base import Base


class Motorista(Base):
    __tablename__ = "motoristas"

    id = Column(Integer, primary_key=True, index=True)

    nome = Column(String(255), nullable=False)
    cpf = Column(String(20), nullable=False, unique=True, index=True)
    rg = Column(String(30), nullable=True)

    cnh = Column(String(30), nullable=True)
    categoria_cnh = Column(String(10), nullable=True)
    validade_cnh = Column(Date, nullable=True)

    telefone = Column(String(30), nullable=True)
    email = Column(String(255), nullable=True)

    transportador_id = Column(Integer, ForeignKey("transportadores.id"), nullable=True)

    ativo = Column(Boolean, nullable=False, default=True)

    criado_em = Column(DateTime(timezone=True), server_default=func.now())
    atualizado_em = Column(DateTime(timezone=True), onupdate=func.now())

    transportador = relationship("Transportador")