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
        return Decimal(valor.replace(",", "."))
    except Exception:
        return Decimal("0")


def texto_xml(elemento, caminho: str, ns: dict) -> str | None:
    encontrado = elemento.find(caminho, ns)

    if encontrado is None:
        return None

    return encontrado.text


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


def ler_xml_nfe(caminho_xml: Path) -> dict:
    try:
        tree = ET.parse(caminho_xml)
        root = tree.getroot()
    except Exception:
        raise ValueError("Não foi possível ler o XML informado.")

    ns = {"nfe": "http://www.portalfiscal.inf.br/nfe"}

    inf_nfe = root.find(".//nfe:infNFe", ns)

    if inf_nfe is None:
        raise ValueError("XML inválido. Não foi encontrada a tag infNFe.")

    chave_nfe = inf_nfe.attrib.get("Id", "").replace("NFe", "")

    numero_nfe = texto_xml(inf_nfe, ".//nfe:ide/nfe:nNF", ns)

    produtos = inf_nfe.findall(".//nfe:det", ns)

    produto_descricao = None
    quantidade_total = Decimal("0")
    valor_total_produtos = Decimal("0")

    for item in produtos:
        descricao = texto_xml(item, ".//nfe:prod/nfe:xProd", ns)
        quantidade = decimal_xml(texto_xml(item, ".//nfe:prod/nfe:qCom", ns))
        valor_produto = decimal_xml(texto_xml(item, ".//nfe:prod/nfe:vProd", ns))

        if not produto_descricao and descricao:
            produto_descricao = descricao

        quantidade_total += quantidade
        valor_total_produtos += valor_produto

    peso_bruto = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:transp/nfe:vol/nfe:pesoB", ns)
    )

    peso_liquido = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:transp/nfe:vol/nfe:pesoL", ns)
    )

    valor_carga = decimal_xml(
        texto_xml(inf_nfe, ".//nfe:total/nfe:ICMSTot/nfe:vNF", ns)
    )

    if valor_carga <= 0:
        valor_carga = valor_total_produtos

    return {
        "chave_nfe": chave_nfe,
        "numero_nfe": numero_nfe,
        "produto": produto_descricao,
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