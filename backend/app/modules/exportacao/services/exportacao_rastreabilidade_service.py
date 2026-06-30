from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.services.exportacao_consumo_service import (
    registrar_movimentacao_consumo,
)


def processar_saida_exportacao(
    db: Session,
    saida: ExportacaoSaida,
):
    itens = saida.itens_exportacao or []

    if not itens:
        raise ValueError(
            f"Saída {saida.numero_nfe or saida.chave_nfe} não possui itens de exportação."
        )

    consumos = []

    for item in itens:
        entrada = (
            db.query(ExportacaoEntrada)
            .filter(
                ExportacaoEntrada.chave_nfe == item.chave_nfe_entrada,
                ExportacaoEntrada.empresa_id == saida.empresa_id,
            )
            .first()
        )

        if not entrada:
            raise ValueError(
                "NF-e de entrada não encontrada para consumo dentro da mesma filial. "
                f"Chave entrada: {item.chave_nfe_entrada}. "
                f"Saída: {saida.numero_nfe or saida.chave_nfe}. "
                f"Empresa ID: {saida.empresa_id}."
            )

        consumo = registrar_movimentacao_consumo(
            db=db,
            entrada=entrada,
            saida=saida,
            numero_re=item.numero_re,
            quantidade_consumida=Decimal(item.quantidade_consumida or 0),
        )

        consumos.append(consumo)

    return consumos