from decimal import Decimal

from sqlalchemy.orm import Session, joinedload

from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada


def _decimal(valor, default: Decimal = Decimal("0")) -> Decimal:
    if valor in [None, ""]:
        return default

    try:
        return Decimal(str(valor))
    except Exception:
        return default


def obter_rastreabilidade_entrada_por_chave(
    db: Session,
    chave_nfe: str,
):
    chave_nfe = "".join(filter(str.isdigit, str(chave_nfe or "")))

    if len(chave_nfe) != 44:
        return {
            "encontrada": False,
            "mensagem": "Chave de entrada inválida.",
            "entrada": None,
            "consumos": [],
        }

    entrada = (
        db.query(ExportacaoEntrada)
        .options(
            joinedload(ExportacaoEntrada.empresa),
            joinedload(ExportacaoEntrada.consumos),
        )
        .filter(ExportacaoEntrada.chave_nfe == chave_nfe)
        .first()
    )

    if not entrada:
        return {
            "encontrada": False,
            "mensagem": "Entrada não localizada no GrainDesk.",
            "entrada": None,
            "consumos": [],
        }

    quantidade_original = _decimal(entrada.quantidade_original)
    quantidade_saldo = _decimal(entrada.quantidade_saldo)
    quantidade_consumida = quantidade_original - quantidade_saldo

    consumos = []

    for consumo in entrada.consumos:
        consumos.append(
            {
                "id": consumo.id,
                "numero_nfe_saida": consumo.numero_nfe_saida,
                "chave_nfe_saida": consumo.chave_nfe_saida,
                "numero_re": consumo.numero_re,
                "quantidade_consumida": _decimal(consumo.quantidade_consumida),
                "criado_em": consumo.criado_em,
            }
        )

    return {
        "encontrada": True,
        "mensagem": "Entrada localizada no GrainDesk.",
        "entrada": {
            "id": entrada.id,
            "empresa": entrada.empresa.razao_social if entrada.empresa else "-",
            "empresa_cidade": entrada.empresa.cidade if entrada.empresa else None,
            "empresa_estado": entrada.empresa.estado if entrada.empresa else None,
            "chave_nfe": entrada.chave_nfe,
            "numero_nfe": entrada.numero_nfe,
            "fornecedor_nome": entrada.fornecedor_nome,
            "fornecedor_cnpj": entrada.fornecedor_cnpj,
            "data_emissao": entrada.data_emissao,
            "data_limite_exportacao": entrada.data_limite_exportacao,
            "situacao_prazo": entrada.situacao_prazo,
            "cfop": entrada.cfop,
            "ncm": entrada.ncm,
            "produto": entrada.produto,
            "quantidade_original": quantidade_original,
            "quantidade_consumida": quantidade_consumida,
            "quantidade_saldo": quantidade_saldo,
            "status": entrada.status,
        },
        "consumos": consumos,
    }