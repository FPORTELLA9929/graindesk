import os
import shutil
import xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path

from fastapi import UploadFile


UPLOAD_XML_DIR = Path("static/uploads/mdfe/xml")
UPLOAD_XML_DIR.mkdir(parents=True, exist_ok=True)


def decimal_xml(valor: str | None) -> Decimal:
    if not valor:
        return Decimal("0")

    try:
        return Decimal(str(valor).replace(",", "."))
    except Exception:
        return Decimal("0")


def texto_xml(elemento, caminho: str, ns: dict) -> str | None:
    encontrado = elemento.find(caminho, ns)

    if encontrado is None or encontrado.text is None:
        return None

    return encontrado.text.strip()


def salvar_xml_temporario(arquivo: UploadFile) -> Path:
    if not arquivo or not arquivo.filename:
        raise ValueError("Arquivo XML não enviado.")

    extensao = Path(arquivo.filename).suffix.lower()

    if extensao != ".xml":
        raise ValueError("O arquivo precisa ser um XML.")

    nome_seguro = arquivo.filename.replace(" ", "_")
    caminho = UPLOAD_XML_DIR / nome_seguro

    with caminho.open("wb") as buffer:
        shutil.copyfileobj(arquivo.file, buffer)

    return caminho


def _somente_numeros(valor: str | None) -> str:
    if not valor:
        return ""

    return "".join(filter(str.isdigit, str(valor)))


def _ncm_valido(ncm: str | None) -> str | None:
    ncm_limpo = _somente_numeros(ncm)

    if len(ncm_limpo) != 8:
        return None

    return ncm_limpo


def _buscar_inf_nfe(root):
    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    inf_nfe = root.find(".//nfe:infNFe", ns)

    if inf_nfe is not None:
        return inf_nfe, ns

    inf_nfe = root.find(".//infNFe")

    if inf_nfe is not None:
        return inf_nfe, {}

    raise ValueError("XML inválido. Não foi encontrada a tag infNFe.")


def ler_xml_nfe(caminho_xml: Path) -> dict:
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()
    except Exception:
        raise ValueError("Não foi possível ler o XML informado.")

    inf_nfe, ns = _buscar_inf_nfe(root)

    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "")
    numero_nfe = texto_xml(inf_nfe, ".//nfe:ide/nfe:nNF", ns)

    if not numero_nfe:
        numero_nfe = texto_xml(inf_nfe, ".//ide/nNF", {})

    produtos = inf_nfe.findall(".//nfe:det", ns)

    if not produtos:
        produtos = inf_nfe.findall(".//det")

    produto_descricao = None
    produto_ncm = None
    quantidade_total = Decimal("0")
    valor_total_produtos = Decimal("0")

    for item in produtos:
        descricao = texto_xml(item, ".//nfe:prod/nfe:xProd", ns)
        ncm = texto_xml(item, ".//nfe:prod/nfe:NCM", ns)
        quantidade = texto_xml(item, ".//nfe:prod/nfe:qCom", ns)
        valor_produto = texto_xml(item, ".//nfe:prod/nfe:vProd", ns)

        if not descricao:
            descricao = texto_xml(item, ".//prod/xProd", {})

        if not ncm:
            ncm = texto_xml(item, ".//prod/NCM", {})

        if not quantidade:
            quantidade = texto_xml(item, ".//prod/qCom", {})

        if not valor_produto:
            valor_produto = texto_xml(item, ".//prod/vProd", {})

        ncm_validado = _ncm_valido(ncm)

        if not produto_descricao and descricao:
            produto_descricao = descricao

        if not produto_ncm and ncm_validado:
            produto_ncm = ncm_validado

        quantidade_total += decimal_xml(quantidade)
        valor_total_produtos += decimal_xml(valor_produto)

    if not produto_ncm:
        raise ValueError(
            "NCM não encontrado no XML da NF-e. "
            "Verifique se o XML é uma NF-e autorizada e possui a tag prod/NCM."
        )

    peso_bruto = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:transp/nfe:vol/nfe:pesoB", ns)
        or texto_xml(inf_nfe, ".//transp/vol/pesoB", {})
    )

    peso_liquido = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:transp/nfe:vol/nfe:pesoL", ns)
        or texto_xml(inf_nfe, ".//transp/vol/pesoL", {})
    )

    valor_carga = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:total/nfe:ICMSTot/nfe:vNF", ns)
        or texto_xml(inf_nfe, ".//total/ICMSTot/vNF", {})
    )

    if valor_carga <= 0:
        valor_carga = valor_total_produtos

    return {
        "chave_nfe": chave_nfe,
        "numero_nfe": numero_nfe,
        "produto": produto_descricao,
        "ncm": produto_ncm,
        "quantidade": quantidade_total,
        "peso_bruto": peso_bruto,
        "peso_liquido": peso_liquido,
        "valor_carga": valor_carga,
        "xml_path": str(caminho_xml),
    }


def importar_xml_nfe(arquivo: UploadFile) -> dict:
    caminho_xml = salvar_xml_temporario(arquivo)

    try:
        return ler_xml_nfe(caminho_xml)
    except Exception as erro:
        if caminho_xml.exists():
            os.remove(caminho_xml)

        if isinstance(erro, ValueError):
            raise erro

        raise ValueError("Erro ao importar XML da NF-e.")