from sqlalchemy.orm import Session

from app.models.fornecedor import Fornecedor
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate


def listar_fornecedores(db: Session):
    return db.query(Fornecedor).order_by(Fornecedor.razao_social.asc()).all()


def buscar_fornecedor(db: Session, fornecedor_id: int):
    return db.query(Fornecedor).filter(Fornecedor.id == fornecedor_id).first()


def buscar_por_cpf_cnpj(db: Session, cpf_cnpj: str):
    return db.query(Fornecedor).filter(Fornecedor.cpf_cnpj == cpf_cnpj).first()


def criar_fornecedor(db: Session, dados: FornecedorCreate):
    fornecedor = Fornecedor(**dados.model_dump())
    db.add(fornecedor)
    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def atualizar_fornecedor(db: Session, fornecedor: Fornecedor, dados: FornecedorUpdate):
    for campo, valor in dados.model_dump().items():
        setattr(fornecedor, campo, valor)

    db.commit()
    db.refresh(fornecedor)
    return fornecedor


def excluir_fornecedor(db: Session, fornecedor: Fornecedor):
    db.delete(fornecedor)
    db.commit()
    return fornecedor