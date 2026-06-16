from sqlalchemy.orm import Session

from app.models.cliente import Cliente
from app.schemas.cliente import ClienteCreate, ClienteUpdate


def listar_clientes(db: Session):
    return db.query(Cliente).order_by(Cliente.razao_social.asc()).all()


def buscar_cliente(db: Session, cliente_id: int):
    return db.query(Cliente).filter(Cliente.id == cliente_id).first()


def buscar_por_cpf_cnpj(db: Session, cpf_cnpj: str):
    return db.query(Cliente).filter(Cliente.cpf_cnpj == cpf_cnpj).first()


def criar_cliente(db: Session, dados: ClienteCreate):
    cliente = Cliente(**dados.model_dump())
    db.add(cliente)
    db.commit()
    db.refresh(cliente)
    return cliente


def atualizar_cliente(db: Session, cliente: Cliente, dados: ClienteUpdate):
    for campo, valor in dados.model_dump().items():
        setattr(cliente, campo, valor)

    db.commit()
    db.refresh(cliente)
    return cliente


def excluir_cliente(db: Session, cliente: Cliente):
    db.delete(cliente)
    db.commit()
    return cliente