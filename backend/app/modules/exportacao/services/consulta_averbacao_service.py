from sqlalchemy.orm import Session

from app.modules.exportacao.services.sefaz_nfe_averbacao_service import (
    consultar_averbacao_sefaz_por_chave,
)


def consultar_averbacao_por_chave(
    db: Session,
    chave: str,
    empresa_id: int,
) -> dict:
    resultado = consultar_averbacao_sefaz_por_chave(
        db=db,
        chave=chave,
        empresa_id=empresa_id,
    )

    return {
        "chave": resultado.chave,
        "numero_due": resultado.numero_due or "-",
        "item_nfe": resultado.item_nfe or "-",
        "item_due": resultado.item_due or "-",
        "quantidade_averbada": resultado.quantidade_averbada or "-",
        "data_averbacao": resultado.data_averbacao or "-",
        "situacao": resultado.situacao,
    }


def consultar_averbacoes_por_chaves(
    db: Session,
    chaves: list[str],
    empresa_id: int,
) -> list[dict]:
    resultados = []

    for chave in chaves:
        resultados.append(
            consultar_averbacao_por_chave(
                db=db,
                chave=chave,
                empresa_id=empresa_id,
            )
        )

    return resultados