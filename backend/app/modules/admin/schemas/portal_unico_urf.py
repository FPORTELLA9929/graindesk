from pydantic import BaseModel


class PortalUnicoURFBase(BaseModel):
    codigo: str
    descricao: str
    ativo: bool = True


class PortalUnicoURFCreate(PortalUnicoURFBase):
    pass


class PortalUnicoURFUpdate(PortalUnicoURFBase):
    pass