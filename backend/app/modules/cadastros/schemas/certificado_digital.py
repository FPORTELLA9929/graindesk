from datetime import datetime

from pydantic import BaseModel


class CertificadoDigitalBase(BaseModel):
    empresa_id: int
    tipo_certificado: str = "A1"
    ativo: bool = True


class CertificadoDigitalCreate(CertificadoDigitalBase):
    senha: str


class CertificadoDigitalUpdate(BaseModel):
    tipo_certificado: str = "A1"
    ativo: bool = True
    senha: str | None = None


class CertificadoDigitalRead(CertificadoDigitalBase):
    id: int
    cnpj_certificado: str
    cnpj_raiz: str
    arquivo_path: str
    criado_em: datetime
    atualizado_em: datetime

    class Config:
        from_attributes = True