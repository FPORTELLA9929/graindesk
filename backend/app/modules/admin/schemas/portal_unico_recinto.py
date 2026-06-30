from pydantic import BaseModel


class PortalUnicoRecintoBase(BaseModel):
    codigo: str
    descricao: str
    ativo: bool = True


class PortalUnicoRecintoCreate(PortalUnicoRecintoBase):
    pass


class PortalUnicoRecintoUpdate(PortalUnicoRecintoBase):
    pass