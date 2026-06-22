from datetime import datetime

from pydantic import BaseModel


class VeiculoBase(BaseModel):
    transportador_id: int
    tipo_veiculo_id: int
    observacao: str | None = None
    ativo: bool = True


class VeiculoCreate(VeiculoBase):
    pass


class VeiculoUpdate(VeiculoBase):
    pass


class VeiculoRead(VeiculoBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True


class VeiculoPlacaBase(BaseModel):
    descricao: str
    placa: str

    renavam: str | None = None
    tara_kg: int | None = None
    capacidade_kg: int | None = None
    capacidade_m3: int | None = None

    cpf_cnpj_proprietario: str | None = None
    rntrc: str | None = None


class VeiculoPlacaCreate(VeiculoPlacaBase):
    pass


class VeiculoPlacaRead(VeiculoPlacaBase):
    id: int

    class Config:
        from_attributes = True