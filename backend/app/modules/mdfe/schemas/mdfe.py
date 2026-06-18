from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class MdfeBase(BaseModel):
    numero: int
    serie: int

    empresa_id: int
    transportador_id: int
    motorista_id: int
    veiculo_id: int
    rota_id: int

    uf_inicio: str
    uf_fim: str

    observacoes: Optional[str] = None


class MdfeCreate(MdfeBase):
    pass


class MdfeUpdate(BaseModel):
    numero: Optional[int] = None
    serie: Optional[int] = None

    empresa_id: Optional[int] = None
    transportador_id: Optional[int] = None
    motorista_id: Optional[int] = None
    veiculo_id: Optional[int] = None
    rota_id: Optional[int] = None

    uf_inicio: Optional[str] = None
    uf_fim: Optional[str] = None

    status: Optional[str] = None

    observacoes: Optional[str] = None


class MdfeRead(MdfeBase):
    id: int
    status: str

    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True