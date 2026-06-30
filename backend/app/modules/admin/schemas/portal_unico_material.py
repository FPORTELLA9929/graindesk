from pydantic import BaseModel


class PortalUnicoMaterialBase(BaseModel):
    ncm: str
    descricao: str
    ativo: bool = True


class PortalUnicoMaterialCreate(PortalUnicoMaterialBase):
    pass


class PortalUnicoMaterialUpdate(PortalUnicoMaterialBase):
    pass