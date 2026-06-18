from sqlalchemy.orm import Session

from app.models.empresa import Empresa
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate


def listar_empresas(db: Session):
    return db.query(Empresa).order_by(Empresa.razao_social.asc()).all()


def buscar_empresa(db: Session, empresa_id: int):
    return db.query(Empresa).filter(Empresa.id == empresa_id).first()


def buscar_por_cnpj(db: Session, cnpj: str):
    return db.query(Empresa).filter(Empresa.cnpj == cnpj).first()


def criar_empresa(db: Session, dados: EmpresaCreate):
    empresa = Empresa(**dados.model_dump())

    db.add(empresa)
    db.commit()
    db.refresh(empresa)

    return empresa


def atualizar_empresa(db: Session, empresa: Empresa, dados: EmpresaUpdate):
    dados_dict = dados.model_dump()

    for campo, valor in dados_dict.items():
        setattr(empresa, campo, valor)

    db.commit()
    db.refresh(empresa)

    return empresa


def atualizar_logo_empresa(db: Session, empresa: Empresa, logo_path: str):
    empresa.logo_path = logo_path

    db.commit()
    db.refresh(empresa)

    return empresa


def excluir_empresa(db: Session, empresa: Empresa):
    db.delete(empresa)
    db.commit()