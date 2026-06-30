from sqlalchemy.orm import Session

from app.modules.portal_unico.models.portal_unico_cct_saldo import (
    PortalUnicoCCTSaldo,
)


def listar_saldos_cct(
    db: Session,
    numero_nfe: str | None = None,
    centro_origem: str | None = None,
    material: str | None = None,
    porto: str | None = None,
    recinto: str | None = None,
    situacao: str | None = None,
    limite: int = 500,
):
    query = db.query(PortalUnicoCCTSaldo)

    if numero_nfe:
        query = query.filter(
            PortalUnicoCCTSaldo.numero_nfe.ilike(f"%{numero_nfe}%")
        )

    if centro_origem:
        query = query.filter(
            PortalUnicoCCTSaldo.centro_origem == centro_origem
        )

    if material:
        query = query.filter(
            PortalUnicoCCTSaldo.material == material
        )

    if porto:
        query = query.filter(
            PortalUnicoCCTSaldo.porto == porto
        )

    if recinto:
        query = query.filter(
            PortalUnicoCCTSaldo.recinto == recinto
        )

    if situacao:
        query = query.filter(
            PortalUnicoCCTSaldo.situacao == situacao
        )

    return (
        query
        .order_by(PortalUnicoCCTSaldo.numero_nfe.desc())
        .limit(limite)
        .all()
    )


def listar_opcoes_filtros_cct(db: Session) -> dict:
    def distintos(campo):
        return [
            valor[0]
            for valor in (
                db.query(campo)
                .filter(campo.isnot(None))
                .filter(campo != "")
                .distinct()
                .order_by(campo.asc())
                .all()
            )
        ]

    return {
        "centros_origem": distintos(PortalUnicoCCTSaldo.centro_origem),
        "materiais": distintos(PortalUnicoCCTSaldo.material),
        "portos": distintos(PortalUnicoCCTSaldo.porto),
        "recintos": distintos(PortalUnicoCCTSaldo.recinto),
        "situacoes": distintos(PortalUnicoCCTSaldo.situacao),
    }