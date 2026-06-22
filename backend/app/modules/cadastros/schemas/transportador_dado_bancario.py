from datetime import datetime

from pydantic import BaseModel


class TransportadorDadoBancarioBase(BaseModel):
    transportador_id: int

    banco_codigo: str | None = None
    banco_nome: str | None = None

    agencia: str | None = None
    conta: str | None = None
    digito_conta: str | None = None

    tipo_conta: str | None = None

    favorecido: str | None = None
    cpf_cnpj_favorecido: str | None = None

    tipo_pix: str | None = None
    chave_pix: str | None = None

    principal: bool = False
    ativo: bool = True


class TransportadorDadoBancarioCreate(TransportadorDadoBancarioBase):
    pass


class TransportadorDadoBancarioUpdate(TransportadorDadoBancarioBase):
    pass


class TransportadorDadoBancarioRead(TransportadorDadoBancarioBase):
    id: int
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True