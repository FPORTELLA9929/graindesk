from datetime import datetime
from decimal import Decimal

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.models.exportacao_saida_item import ExportacaoSaidaItem
from app.modules.exportacao.services.exportacao_rastreabilidade_service import (
    processar_saida_exportacao,
)
from app.modules.exportacao.services.exportacao_saida_xml_service import (
    ler_xml_saida_exportacao,
)


def _data_xml_para_datetime(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except Exception:
        return None


def _somente_digitos(valor: str | None) -> str:
    if not valor:
        return ""

    return "".join(filter(str.isdigit, str(valor)))


def obter_empresa_por_cnpj_emitente(
    db: Session,
    cnpj_emitente: str | None,
):
    cnpj_limpo = _somente_digitos(cnpj_emitente)

    if not cnpj_limpo:
        raise ValueError("XML não possui CNPJ do emitente.")

    empresa = (
        db.query(Empresa)
        .filter(Empresa.cnpj == cnpj_limpo)
        .first()
    )

    if not empresa:
        raise ValueError(
            "Empresa exportadora não encontrada no cadastro para o CNPJ do emitente do XML: "
            f"{cnpj_limpo}."
        )

    if not empresa.ativo:
        raise ValueError(
            "Empresa exportadora encontrada, porém está inativa: "
            f"{empresa.razao_social} - {cnpj_limpo}."
        )

    return empresa


async def importar_xml_saida_exportacao(
    db: Session,
    empresa_id: int | None,
    arquivo_xml: UploadFile,
):
    conteudo = await arquivo_xml.read()
    dados = ler_xml_saida_exportacao(conteudo)

    empresa = obter_empresa_por_cnpj_emitente(
        db=db,
        cnpj_emitente=dados.get("emitente_cnpj"),
    )

    if empresa_id and empresa.id != empresa_id:
        raise ValueError(
            "A empresa selecionada não corresponde ao emitente da NF-e de exportação. "
            f"Empresa selecionada ID: {empresa_id}. "
            f"Emitente do XML: {dados.get('emitente_nome') or '-'} "
            f"({dados.get('emitente_cnpj') or '-'})."
        )

    existente = (
        db.query(ExportacaoSaida)
        .filter(ExportacaoSaida.chave_nfe == dados["chave_nfe"])
        .first()
    )

    if existente:
        return {
            "status": "duplicada",
            "mensagem": "NF-e de exportação já importada.",
            "saida": existente,
            "consumos": [],
            "itens": list(existente.itens_exportacao or []),
        }

    if not dados["exportacoes_indiretas"]:
        return {
            "status": "sem_export_ind",
            "mensagem": "NF-e de exportação não possui detExport/exportInd.",
            "saida": None,
            "consumos": [],
            "itens": [],
        }

    saida = ExportacaoSaida(
        empresa_id=empresa.id,
        chave_nfe=dados["chave_nfe"],
        numero_nfe=dados["numero_nfe"],
        serie=dados["serie"],
        destinatario_nome=dados["destinatario_nome"],
        destinatario_documento=dados["destinatario_documento"],
        data_emissao=_data_xml_para_datetime(dados["data_emissao"]),
        cfop=dados["cfop"],
        ncm=dados["ncm"],
        produto=dados["produto"],
        quantidade_exportada=Decimal(dados["quantidade_exportada"] or 0),
        valor_exportado=Decimal(dados["valor_exportado"] or 0),
        status="processada",
    )

    db.add(saida)
    db.flush()

    itens = []

    for item in dados["exportacoes_indiretas"]:
        saida_item = ExportacaoSaidaItem(
            saida_id=saida.id,
            chave_nfe_saida=saida.chave_nfe,
            numero_nfe_saida=saida.numero_nfe,
            chave_nfe_entrada=item["chave_nfe_entrada"],
            numero_re=item["numero_re"],
            quantidade_consumida=Decimal(item["quantidade_consumida"] or 0),
        )

        db.add(saida_item)
        db.flush()

        itens.append(saida_item)

    consumos = processar_saida_exportacao(
        db=db,
        saida=saida,
    )

    db.commit()
    db.refresh(saida)

    return {
        "status": "importada",
        "mensagem": "NF-e de exportação importada, itens gravados e saldos consumidos com sucesso.",
        "saida": saida,
        "consumos": consumos,
        "itens": itens,
    }