from decimal import Decimal, ROUND_HALF_UP

from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.modules.cadastros.models.rota import Rota
from app.modules.cadastros.models.veiculo import Veiculo
from app.modules.cadastros.models.tipo_veiculo import TipoVeiculo

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.models.mdfe_documento import MdfeDocumento
from app.modules.mdfe.services.mdfe_xml_service import importar_xml_nfe


def moeda(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def buscar_documento_por_chave(
    db: Session,
    mdfe_id: int,
    chave_nfe: str,
):
    return (
        db.query(MdfeDocumento)
        .filter(MdfeDocumento.mdfe_id == mdfe_id)
        .filter(MdfeDocumento.chave_nfe == chave_nfe)
        .first()
    )


def importar_documento_xml_no_mdfe(
    db: Session,
    mdfe_id: int,
    arquivo_xml: UploadFile,
):
    mdfe = db.query(Mdfe).filter(Mdfe.id == mdfe_id).first()

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    rota = db.query(Rota).filter(Rota.id == mdfe.rota_id).first()

    if not rota:
        raise ValueError("Rota não encontrada.")

    veiculo = db.query(Veiculo).filter(Veiculo.id == mdfe.veiculo_id).first()

    if not veiculo:
        raise ValueError("Veículo não encontrado.")

    tipo_veiculo = (
        db.query(TipoVeiculo)
        .filter(TipoVeiculo.id == veiculo.tipo_veiculo_id)
        .first()
    )

    if not tipo_veiculo:
        raise ValueError("Tipo de veículo não encontrado.")

    dados_xml = importar_xml_nfe(arquivo_xml)

    chave_nfe = dados_xml.get("chave_nfe")

    if not chave_nfe:
        raise ValueError("Chave da NF-e não encontrada no XML.")

    documento_existente = buscar_documento_por_chave(
        db=db,
        mdfe_id=mdfe.id,
        chave_nfe=chave_nfe,
    )

    if documento_existente:
        return documento_existente

    peso_liquido = dados_xml.get("peso_liquido") or Decimal("0")
    tarifa_rota = rota.tarifa or Decimal("0")
    pedagio_por_eixo = rota.valor_pedagio_por_eixo or Decimal("0")
    quantidade_eixos = tipo_veiculo.quantidade_eixos or 0

    peso_toneladas = peso_liquido / Decimal("1000")

    frete_base = moeda(peso_toneladas * tarifa_rota)

    if rota.possui_pedagio:
        pedagio_total = moeda(pedagio_por_eixo * Decimal(quantidade_eixos))
    else:
        pedagio_total = Decimal("0.00")

    frete_total = moeda(frete_base + pedagio_total)

    documento = MdfeDocumento(
        mdfe_id=mdfe.id,
        chave_nfe=chave_nfe,
        numero_nfe=dados_xml.get("numero_nfe"),
        produto=dados_xml.get("produto"),
        ncm=dados_xml.get("ncm"),
        quantidade=dados_xml.get("quantidade"),
        peso_bruto=dados_xml.get("peso_bruto"),
        peso_liquido=peso_liquido,
        valor_carga=dados_xml.get("valor_carga"),
        tarifa_rota=tarifa_rota,
        pedagio_por_eixo=pedagio_por_eixo,
        frete_base=frete_base,
        pedagio_total=pedagio_total,
        frete_total=frete_total,
        xml_path=dados_xml.get("xml_path"),
    )

    db.add(documento)
    db.commit()
    db.refresh(documento)

    return documento