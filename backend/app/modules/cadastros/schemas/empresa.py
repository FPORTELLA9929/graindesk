from datetime import datetime

from pydantic import BaseModel, Field


class EmpresaBase(BaseModel):
    razao_social: str = Field(..., max_length=255)
    nome_fantasia: str | None = None

    cnpj: str = Field(..., max_length=20)
    inscricao_estadual: str | None = None

    logradouro: str | None = None
    numero: str | None = None
    bairro: str | None = None

    municipio_id: int | None = None

    cidade: str | None = None
    estado: str | None = None
    cep: str | None = None

    telefone: str | None = None
    email: str | None = None

    ativo: bool = True


class EmpresaCreate(EmpresaBase):
    pass


class EmpresaUpdate(EmpresaBase):
    pass


class EmpresaRead(EmpresaBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True