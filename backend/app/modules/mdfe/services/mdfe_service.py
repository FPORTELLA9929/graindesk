from sqlalchemy.orm import Session

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.schemas.mdfe import MdfeCreate, MdfeUpdate


def listar_mdfes(db: Session):
    return (
        db.query(Mdfe)
        .order_by(Mdfe.id.desc())
        .all()
    )


def buscar_mdfe(db: Session, mdfe_id: int):
    return (
        db.query(Mdfe)
        .filter(Mdfe.id == mdfe_id)
        .first()
    )


def criar_mdfe(db: Session, dados: MdfeCreate):
    mdfe = Mdfe(
        numero=dados.numero,
        serie=dados.serie,
        empresa_id=dados.empresa_id,
        transportador_id=dados.transportador_id,
        motorista_id=dados.motorista_id,
        veiculo_id=dados.veiculo_id,
        rota_id=dados.rota_id,
        uf_inicio=dados.uf_inicio,
        uf_fim=dados.uf_fim,
        status="rascunho",
        observacoes=dados.observacoes,
    )

    db.add(mdfe)
    db.commit()
    db.refresh(mdfe)

    return mdfe


def atualizar_mdfe(db: Session, mdfe_id: int, dados: MdfeUpdate):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        return None

    if mdfe.status != "rascunho":
        raise ValueError("Somente MDF-e em rascunho pode ser editado.")

    campos = dados.model_dump(exclude_unset=True)

    for campo, valor in campos.items():
        setattr(mdfe, campo, valor)

    db.commit()
    db.refresh(mdfe)

    return mdfe


def excluir_mdfe(db: Session, mdfe_id: int):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        return False

    if mdfe.status != "rascunho":
        raise ValueError("Somente MDF-e em rascunho pode ser excluído.")

    db.delete(mdfe)
    db.commit()

    return True