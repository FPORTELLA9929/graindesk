from decimal import Decimal

from sqlalchemy.orm import Session

from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo
from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida


def calcular_quantidade_consumida_entrada(
    db: Session,
    entrada_id: int,
) -> Decimal:
    consumos = (
        db.query(ExportacaoConsumo)
        .filter(ExportacaoConsumo.entrada_id == entrada_id)
        .all()
    )

    total = Decimal("0")

    for consumo in consumos:
        total += Decimal(consumo.quantidade_consumida or 0)

    return total


def recalcular_saldo_entrada(
    db: Session,
    entrada: ExportacaoEntrada,
):
    consumido = calcular_quantidade_consumida_entrada(
        db=db,
        entrada_id=entrada.id,
    )

    saldo = Decimal(entrada.quantidade_original or 0) - consumido

    if saldo < 0:
        raise ValueError("Saldo da entrada ficou negativo.")

    entrada.quantidade_saldo = saldo

    if saldo == 0:
        entrada.status = "consumida"
    elif saldo < Decimal(entrada.quantidade_original or 0):
        entrada.status = "parcial"
    else:
        entrada.status = "disponivel"

    db.add(entrada)

    return entrada


def registrar_movimentacao_consumo(
    db: Session,
    entrada: ExportacaoEntrada,
    saida: ExportacaoSaida,
    numero_re: str | None,
    quantidade_consumida: Decimal,
):
    quantidade_consumida = Decimal(quantidade_consumida or 0)

    if quantidade_consumida <= 0:
        raise ValueError("Quantidade consumida deve ser maior que zero.")

    saldo_atual = Decimal(entrada.quantidade_saldo or 0)

    if quantidade_consumida > saldo_atual:
        raise ValueError(
            f"Saldo insuficiente para a NF-e {entrada.numero_nfe}. "
            f"Saldo atual: {saldo_atual}. "
            f"Quantidade solicitada: {quantidade_consumida}."
        )

    consumo = ExportacaoConsumo(
        entrada_id=entrada.id,
        saida_id=saida.id,
        chave_nfe_entrada=entrada.chave_nfe,
        chave_nfe_saida=saida.chave_nfe,
        numero_nfe_entrada=entrada.numero_nfe,
        numero_nfe_saida=saida.numero_nfe,
        numero_re=numero_re,
        quantidade_consumida=quantidade_consumida,
    )

    db.add(consumo)
    db.flush()

    recalcular_saldo_entrada(
        db=db,
        entrada=entrada,
    )

    return consumo