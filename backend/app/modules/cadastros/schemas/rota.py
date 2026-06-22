from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class RotaBase(BaseModel):
    municipio_origem_id: int
    municipio_destino_id: int

    distancia_km: Decimal | None = Field(default=None)
    tarifa: Decimal | None = Field(default=None)

    possui_pedagio: bool = False
    valor_pedagio_por_eixo: Decimal | None = Field(default=None)

    observacao: str | None = None

    vigencia_inicio: date | None = None
    vigencia_fim: date | None = None

    ativo: bool = True


class RotaCreate(RotaBase):
    pass


class RotaUpdate(RotaBase):
    pass


class RotaRead(RotaBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True