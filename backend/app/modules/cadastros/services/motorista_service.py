import re

from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.modules.cadastros.models.motorista import Motorista
from app.modules.cadastros.models.transportador import Transportador
from app.modules.cadastros.schemas.motorista import (
    MotoristaCreate,
    MotoristaUpdate,
)


def somente_numeros(valor: str | None):
    if not valor:
        return ""

    return re.sub(r"\D", "", valor)


def listar_motoristas(
    db: Session,
    busca: str | None = None,
    transportador_id: int | None = None,
    status: str | None = None,
):
    query = (
        db.query(Motorista)
        .options(joinedload(Motorista.transportador))
        .outerjoin(Transportador, Motorista.transportador_id == Transportador.id)
    )

    if busca:
        busca_limpa = busca.strip()
        busca_numeros = somente_numeros(busca_limpa)

        filtros = [
            Motorista.nome.ilike(f"%{busca_limpa}%"),
            Motorista.cnh.ilike(f"%{busca_limpa}%"),
            Transportador.nome_razao_social.ilike(f"%{busca_limpa}%"),
        ]

        if busca_numeros:
            filtros.append(Motorista.cpf.ilike(f"%{busca_numeros}%"))

        query = query.filter(or_(*filtros))

    if transportador_id:
        query = query.filter(Motorista.transportador_id == transportador_id)

    if status == "ativo":
        query = query.filter(Motorista.ativo == True)

    if status == "inativo":
        query = query.filter(Motorista.ativo == False)

    return query.order_by(Motorista.nome.asc()).all()


def buscar_motorista(db: Session, motorista_id: int):
    return (
        db.query(Motorista)
        .options(joinedload(Motorista.transportador))
        .filter(Motorista.id == motorista_id)
        .first()
    )


def buscar_por_cpf(db: Session, cpf: str):
    cpf_limpo = somente_numeros(cpf)

    return db.query(Motorista).filter(Motorista.cpf == cpf_limpo).first()


def criar_motorista(db: Session, dados: MotoristaCreate):
    motorista = Motorista(**dados.model_dump())
    db.add(motorista)
    db.commit()
    db.refresh(motorista)
    return motorista


def atualizar_motorista(db: Session, motorista: Motorista, dados: MotoristaUpdate):
    for campo, valor in dados.model_dump().items():
        setattr(motorista, campo, valor)

    db.commit()
    db.refresh(motorista)
    return motorista


def excluir_motorista(db: Session, motorista: Motorista):
    db.delete(motorista)
    db.commit()
    return motorista