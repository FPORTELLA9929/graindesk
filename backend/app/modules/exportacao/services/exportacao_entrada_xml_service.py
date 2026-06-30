from decimal import Decimal
from xml.etree import ElementTree as ET


NFE_NS = {
    "nfe": "http://www.portalfiscal.inf.br/nfe",
}


UNIDADES_TONELADA = {
    "TON",
    "T",
    "TN",
    "TONELADA",
    "TONELADAS",
}


CFOPS_USAR_DEST_COMO_FORNECEDOR = {
    "1501",
    "2501",
}


PRODUTOS_PADRAO_NCM = {
    "12019000": "SOJA EM GRÃOS",
    "10059010": "MILHO EM GRÃOS",
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


def _produto_padronizado_por_ncm(
    ncm: str | None,
    produto_original: str | None,
) -> str | None:
    ncm_normalizado = _normalizar_ncm(ncm)

    if ncm_normalizado in PRODUTOS_PADRAO_NCM:
        return PRODUTOS_PADRAO_NCM[ncm_normalizado]

    return produto_original


def _converter_quantidade_para_kg(quantidade: Decimal, unidade: str | None) -> Decimal:
    unidade_normalizada = (unidade or "").strip().upper()

    if unidade_normalizada in UNIDADES_TONELADA:
        return quantidade * Decimal("1000")

    return quantidade


def ler_xml_entrada_equiparada(conteudo_xml: bytes) -> dict:
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
    destinatario_cnpj = _normalizar_documento(_documento_pessoa(dest))

    quantidade_total = Decimal("0")
    valor_produtos = Decimal("0")

    primeiro_cfop = None
    primeiro_ncm = None
    primeiro_produto = None

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

        quantidade = _decimal(_texto(prod, "nfe:qCom"))
        unidade = _texto(prod, "nfe:uCom")

        quantidade_total += _converter_quantidade_para_kg(
            quantidade=quantidade,
            unidade=unidade,
        )

        valor_produtos += _decimal(_texto(prod, "nfe:vProd"))

    produto_padronizado = _produto_padronizado_por_ncm(
        ncm=primeiro_ncm,
        produto_original=primeiro_produto,
    )

    if primeiro_cfop in CFOPS_USAR_DEST_COMO_FORNECEDOR:
        fornecedor_nome = destinatario_nome
        fornecedor_cnpj = destinatario_cnpj
    else:
        fornecedor_nome = emitente_nome
        fornecedor_cnpj = emitente_cnpj

    valor_total = _decimal(_texto(total, "nfe:vNF"))

    return {
        "chave_nfe": chave_nfe,
        "numero_nfe": numero_nfe,
        "serie": serie,
        "data_emissao": data_emissao,
        "emitente_nome": emitente_nome,
        "emitente_cnpj": emitente_cnpj,
        "destinatario_nome": destinatario_nome,
        "destinatario_cnpj": destinatario_cnpj,
        "fornecedor_nome": fornecedor_nome,
        "fornecedor_cnpj": fornecedor_cnpj,
        "cfop": primeiro_cfop,
        "ncm": primeiro_ncm,
        "produto": produto_padronizado,
        "quantidade_original": quantidade_total,
        "quantidade_saldo": quantidade_total,
        "valor_original": valor_total or valor_produtos,
    }