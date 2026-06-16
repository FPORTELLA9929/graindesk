from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClienteBase(BaseModel):
    razao_social: str
    nome_fantasia: Optional[str] = None
    cpf_cnpj: str
    inscricao_estadual: Optional[str] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    logradouro: Optional[str] = None
    numero: Optional[str] = None
    bairro: Optional[str] = None
    cidade: Optional[str] = None
    estado: Optional[str] = None
    cep: Optional[str] = None
    ativo: bool = True


class ClienteCreate(ClienteBase):
    pass


class ClienteUpdate(ClienteBase):
    pass


class ClienteRead(ClienteBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True