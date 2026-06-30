from decimal import Decimal
from xml.etree import ElementTree as ET


NFE_NS = {
    "nfe": "http://www.portalfiscal.inf.br/nfe",
}


def _texto(elemento, caminho: str, default: str | None = None):
    if elemento is None:
        return default

    achado = elemento.find(caminho, NFE_NS)

    if achado is None or achado.text is None:
        return default

    return achado.text.strip()


def _decimal(valor, default: Decimal = Decimal("0")) -> Decimal:
    if valor is None or valor == "":
        return default

    try:
        return Decimal(str(valor))
    except Exception:
        return default


def _documento_pessoa(elemento):
    return (
        _texto(elemento, "nfe:CNPJ")
        or _texto(elemento, "nfe:CPF")
        or _texto(elemento, "nfe:idEstrangeiro")
    )


def _normalizar_documento(valor: str | None) -> str | None:
    if not valor:
        return None

    documento = "".join(filter(str.isdigit, str(valor)))

    return documento or None


def _normalizar_ncm(ncm: str | None) -> str | None:
    if not ncm:
        return None

    return "".join(filter(str.isdigit, ncm))


def ler_xml_saida_exportacao(conteudo_xml: bytes) -> dict:
    raiz = ET.fromstring(conteudo_xml)

    inf_nfe = raiz.find(".//nfe:infNFe", NFE_NS)

    if inf_nfe is None:
        raise ValueError("XML inválido: tag infNFe não encontrada.")

    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "").strip()

    ide = inf_nfe.find("nfe:ide", NFE_NS)
    emit = inf_nfe.find("nfe:emit", NFE_NS)
    dest = inf_nfe.find("nfe:dest", NFE_NS)
    total = inf_nfe.find("nfe:total/nfe:ICMSTot", NFE_NS)

    numero_nfe = _texto(ide, "nfe:nNF")
    serie = _texto(ide, "nfe:serie")
    data_emissao = _texto(ide, "nfe:dhEmi") or _texto(ide, "nfe:dEmi")

    emitente_nome = _texto(emit, "nfe:xNome")
    emitente_cnpj = _normalizar_documento(_documento_pessoa(emit))

    destinatario_nome = _texto(dest, "nfe:xNome")
    destinatario_documento = _normalizar_documento(
        _documento_pessoa(dest)
    )

    quantidade_exportada = Decimal("0")
    valor_produtos = Decimal("0")

    primeiro_cfop = None
    primeiro_ncm = None
    primeiro_produto = None

    exportacoes_indiretas = []

    for det in inf_nfe.findall("nfe:det", NFE_NS):
        prod = det.find("nfe:prod", NFE_NS)

        if prod is None:
            continue

        if primeiro_cfop is None:
            primeiro_cfop = _texto(prod, "nfe:CFOP")

        if primeiro_ncm is None:
            primeiro_ncm = _normalizar_ncm(_texto(prod, "nfe:NCM"))

        if primeiro_produto is None:
            primeiro_produto = _texto(prod, "nfe:xProd")

        quantidade_exportada += _decimal(_texto(prod, "nfe:qCom"))
        valor_produtos += _decimal(_texto(prod, "nfe:vProd"))

        for export_ind in prod.findall("nfe:detExport/nfe:exportInd", NFE_NS):
            exportacoes_indiretas.append(
                {
                    "numero_re": _texto(export_ind, "nfe:nRE"),
                    "chave_nfe_entrada": _texto(export_ind, "nfe:chNFe"),
                    "quantidade_consumida": _decimal(
                        _texto(export_ind, "nfe:qExport")
                    ),
                }
            )

    valor_total = _decimal(_texto(total, "nfe:vNF"))

    return {
        "chave_nfe": chave_nfe,
        "numero_nfe": numero_nfe,
        "serie": serie,
        "data_emissao": data_emissao,
        "emitente_nome": emitente_nome,
        "emitente_cnpj": emitente_cnpj,
        "destinatario_nome": destinatario_nome,
        "destinatario_documento": destinatario_documento,
        "cfop": primeiro_cfop,
        "ncm": primeiro_ncm,
        "produto": primeiro_produto,
        "quantidade_exportada": quantidade_exportada,
        "valor_exportado": valor_total or valor_produtos,
        "exportacoes_indiretas": exportacoes_indiretas,
    }