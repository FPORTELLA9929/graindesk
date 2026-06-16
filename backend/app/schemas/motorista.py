from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel


class MotoristaBase(BaseModel):
    nome: str
    cpf: str
    rg: Optional[str] = None
    cnh: str
    categoria_cnh: Optional[str] = None
    validade_cnh: Optional[date] = None
    telefone: Optional[str] = None
    email: Optional[str] = None
    transportador_id: Optional[int] = None
    ativo: bool = True


class MotoristaCreate(MotoristaBase):
    pass


class MotoristaUpdate(MotoristaBase):
    pass


class MotoristaRead(MotoristaBase):
    id: int
    criado_em: Optional[datetime] = None
    atualizado_em: Optional[datetime] = None

    class Config:
        from_attributes = True