from decimal import Decimal, InvalidOperation

from sqlalchemy.orm import Session

from app.modules.admin.models.portal_unico_material import (
    PortalUnicoMaterial,
)


REGRAS_CONVERSAO = {
    "10059010": Decimal("1"),        # Milho
    "12019000": Decimal("1000"),     # Soja
    "10019900": Decimal("1"),        # Trigo
}


def _decimal(valor) -> Decimal:
    if valor in [None, ""]:
        return Decimal("0")

    try:
        return Decimal(str(valor).replace(",", "."))
    except (InvalidOperation, ValueError):
        return Decimal("0")


def obter_fator_conversao(
    db: Session,
    ncm: str | None,
) -> Decimal:
    """
    Retorna o fator de conversão para o NCM.

    A existência do NCM é validada no cadastro de materiais
    do Portal Único para evitar conversões de materiais
    inexistentes.
    """

    if not ncm:
        return Decimal("1")

    material = (
        db.query(PortalUnicoMaterial)
        .filter(
            PortalUnicoMaterial.ncm == str(ncm),
            PortalUnicoMaterial.ativo == True,
        )
        .first()
    )

    if not material:
        return Decimal("1")

    return REGRAS_CONVERSAO.get(
        material.ncm,
        Decimal("1"),
    )


def normalizar_peso_portal_unico(
    db: Session,
    valor,
    ncm: str | None,
) -> Decimal:
    """
    Converte qualquer peso retornado pelo Portal Único para KG.

    Exemplos:

    Soja
        50      -> 50000
        0,500   -> 500
        0,050   -> 50
        0,005   -> 5

    Milho
        41350 -> 41350

    Trigo
        28120 -> 28120
    """

    peso = _decimal(valor)

    fator = obter_fator_conversao(
        db=db,
        ncm=ncm,
    )

    return (peso * fator).quantize(Decimal("1"))