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


def excluir_por_transportador(
    db: Session,
    transportador_id: int,
    commit: bool = True,
):
    (
        db.query(TransportadorDadoBancario)
        .filter(TransportadorDadoBancario.transportador_id == transportador_id)
        .delete(synchronize_session=False)
    )

    if commit:
        db.commit()
    else:
        db.flush()


def criar_dado_bancario(
    db: Session,
    dados: TransportadorDadoBancarioCreate,
    commit: bool = True,
):
    dado = TransportadorDadoBancario(**dados.model_dump())

    db.add(dado)

    if commit:
        db.commit()
        db.refresh(dado)
    else:
        db.flush()

    return dado


def criar_varios_dados_bancarios(
    db: Session,
    dados_bancarios: list[TransportadorDadoBancarioCreate],
    commit: bool = True,
):
    dados = [
        TransportadorDadoBancario(**dado.model_dump())
        for dado in dados_bancarios
    ]

    if dados:
        db.add_all(dados)

    if commit:
        db.commit()
        for dado in dados:
            db.refresh(dado)
    else:
        db.flush()

    return dados