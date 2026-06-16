from sqlalchemy.orm import Session

from app.models.transportador_dado_bancario import TransportadorDadoBancario
from app.schemas.transportador_dado_bancario import (
    TransportadorDadoBancarioCreate,
)


def listar_por_transportador(db: Session, transportador_id: int):
    return (
        db.query(TransportadorDadoBancario)
        .filter(TransportadorDadoBancario.transportador_id == transportador_id)
        .order_by(
            TransportadorDadoBancario.principal.desc(),
            TransportadorDadoBancario.id.asc(),
        )
        .all()
    )


def excluir_por_transportador(db: Session, transportador_id: int):
    (
        db.query(TransportadorDadoBancario)
        .filter(TransportadorDadoBancario.transportador_id == transportador_id)
        .delete()
    )
    db.commit()


def criar_dado_bancario(db: Session, dados: TransportadorDadoBancarioCreate):
    dado = TransportadorDadoBancario(**dados.model_dump())

    db.add(dado)
    db.commit()
    db.refresh(dado)

    return dado