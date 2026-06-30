from sqlalchemy.orm import Session, joinedload

from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo


def listar_consumos_por_chave_cct(
    db: Session,
    chave: str,
):
    if not chave:
        return []

    return (
        db.query(ExportacaoConsumo)
        .options(joinedload(ExportacaoConsumo.saida))
        .filter(ExportacaoConsumo.chave_nfe_entrada == chave)
        .order_by(ExportacaoConsumo.criado_em.desc())
        .all()
    )