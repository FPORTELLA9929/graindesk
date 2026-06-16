from datetime import datetime

from pydantic import BaseModel, Field


class UsuarioCreate(BaseModel):
    nome: str = Field(..., max_length=255)
    empresa: str = Field(..., max_length=255)
    cnpj: str = Field(..., max_length=20)
    email: str = Field(..., max_length=255)
    telefone: str | None = None
    cargo: str | None = None
    senha: str = Field(..., min_length=6)
    confirmar_senha: str = Field(..., min_length=6)


class UsuarioRead(BaseModel):
    id: int
    nome: str
    empresa: str
    cnpj: str
    email: str
    telefone: str | None = None
    cargo: str | None = None
    perfil: str
    status: str
    ativo: bool
    criado_em: datetime
    atualizado_em: datetime
    ultimo_login: datetime | None = None

    class Config:
        from_attributes = True