from pathlib import Path

from lxml import etree


PASTA_SCHEMAS = Path("app/modules/mdfe/xml/schemas")
PASTA_XML_GERADOS = Path("app/modules/mdfe/xml/gerados")
PASTA_XML_ASSINADOS = Path("app/modules/mdfe/xml/assinados")


def localizar_schema_principal() -> Path:
    possiveis = [
        "mdfe_v3.00.xsd",
        "MDFe_v3.00.xsd",
        "mdfe_v3.00b.xsd",
        "MDFe_v3.00b.xsd",
    ]

    for nome in possiveis:
        caminho = PASTA_SCHEMAS / nome
        if caminho.exists():
            return caminho

    arquivos = list(PASTA_SCHEMAS.glob("*.xsd"))

    if not arquivos:
        raise ValueError("Nenhum arquivo XSD encontrado na pasta de schemas.")

    raise ValueError(
        "Schema principal do MDF-e não encontrado. "
        "Verifique se existe mdfe_v3.00.xsd na pasta de schemas."
    )


def localizar_xml_mdfe(mdfe_id: int) -> Path:
    caminho_assinado = PASTA_XML_ASSINADOS / f"mdfe_{mdfe_id}_assinado.xml"

    if caminho_assinado.exists():
        return caminho_assinado

    assinados = list(PASTA_XML_ASSINADOS.glob(f"*{mdfe_id}*assinado*.xml"))

    if assinados:
        return assinados[0]

    caminho_gerado = PASTA_XML_GERADOS / f"mdfe_{mdfe_id}.xml"

    if caminho_gerado.exists():
        return caminho_gerado

    gerados = list(PASTA_XML_GERADOS.glob(f"*{mdfe_id}*.xml"))

    if gerados:
        return gerados[0]

    raise ValueError(
        "XML do MDF-e não encontrado. Gere ou assine o XML primeiro."
    )


def validar_xml_mdfe(mdfe_id: int) -> dict:
    caminho_xml = localizar_xml_mdfe(mdfe_id)
    caminho_schema = localizar_schema_principal()

    parser = etree.XMLParser(remove_blank_text=True)

    try:
        schema_doc = etree.parse(str(caminho_schema), parser)
        schema = etree.XMLSchema(schema_doc)
    except Exception as erro:
        raise ValueError(f"Erro ao carregar schema XSD: {erro}")

    try:
        xml_doc = etree.parse(str(caminho_xml), parser)
    except Exception as erro:
        raise ValueError(f"Erro ao ler XML: {erro}")

    valido = schema.validate(xml_doc)

    erros = []

    if not valido:
        for erro in schema.error_log:
            erros.append(
                {
                    "linha": erro.line,
                    "coluna": erro.column,
                    "mensagem": erro.message,
                }
            )

    return {
        "valido": valido,
        "xml": str(caminho_xml),
        "schema": str(caminho_schema),
        "erros": erros,
    }