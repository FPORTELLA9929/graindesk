from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class TipoVeiculoBase(BaseModel):
    descricao: str

    quantidade_eixos: int
    quantidade_placas: int = 1

    capacidade_kg: Decimal | None = Field(default=None)
    capacidade_m3: Decimal | None = Field(default=None)

    ativo: bool = True


class TipoVeiculoCreate(TipoVeiculoBase):
    pass


class TipoVeiculoUpdate(TipoVeiculoBase):
    pass


class TipoVeiculoRead(TipoVeiculoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True