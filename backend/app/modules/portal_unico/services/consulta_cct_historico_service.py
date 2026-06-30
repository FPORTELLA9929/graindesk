from sqlalchemy.orm import Session, joinedload

from app.modules.portal_unico.models.portal_unico_consulta_cct import (
    PortalUnicoConsultaCCT,
)


def listar_consultas_cct(
    db: Session,
    limite: int = 50,
):
    return (
        db.query(PortalUnicoConsultaCCT)
        .order_by(PortalUnicoConsultaCCT.criado_em.desc())
        .limit(limite)
        .all()
    )


def obter_consulta_cct(
    db: Session,
    consulta_id: int,
):
    return (
        db.query(PortalUnicoConsultaCCT)
        .options(
            joinedload(PortalUnicoConsultaCCT.itens),
        )
        .filter(PortalUnicoConsultaCCT.id == consulta_id)
        .first()
    )