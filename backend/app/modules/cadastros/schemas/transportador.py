from datetime import datetime

from pydantic import BaseModel


class TransportadorBase(BaseModel):
    tipo_pessoa: str

    nome_razao_social: str
    nome_fantasia: str | None = None

    cpf_cnpj: str
    rg_ie: str | None = None

    rntrc: str | None = None
    tipo_transportador: str | None = None
    antt_ativa: bool = True

    telefone: str | None = None
    email: str | None = None

    municipio_id: int

    endereco: str | None = None

    ativo: bool = True


class TransportadorCreate(TransportadorBase):
    pass


class TransportadorUpdate(TransportadorBase):
    pass


class TransportadorRead(TransportadorBase):
    id: int

    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True