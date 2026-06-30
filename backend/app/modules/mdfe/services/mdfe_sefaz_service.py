from pathlib import Path
import base64
import gzip

import requests
from lxml import etree
from requests_pkcs12 import Pkcs12Adapter
from sqlalchemy.orm import Session

from app.modules.admin.services.certificado_digital_service import (
    descriptografar_senha,
    obter_certificado_por_cnpj,
)
from app.modules.mdfe.models.mdfe import Mdfe


URL_RECEPCAO_HOMOLOGACAO = (
    "https://mdfe-homologacao.svrs.rs.gov.br/ws/MDFeRecepcaoSinc/MDFeRecepcaoSinc.asmx"
)

SOAP_ACTION_RECEPCAO = (
    "http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoSinc/mdfeRecepcao"
)

PASTA_DEBUG = Path("app/modules/mdfe/xml/assinados")


def _compactar_base64(xml: str) -> str:
    dados = xml.encode("utf-8")
    compactado = gzip.compress(dados, compresslevel=9, mtime=0)
    return base64.b64encode(compactado).decode("ascii")


def _descompactar_base64(conteudo: str) -> str:
    try:
        dados = base64.b64decode(conteudo)
        descompactado = gzip.decompress(dados)
        return descompactado.decode("utf-8")
    except Exception:
        return conteudo


def _montar_envelope_recepcao(dados_compactados_base64: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
                 xmlns:xsd="http://www.w3.org/2001/XMLSchema"
                 xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
    <soap12:Body>
        <mdfeDadosMsg xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoSinc">
            {dados_compactados_base64}
        </mdfeDadosMsg>
    </soap12:Body>
</soap12:Envelope>"""


def _carregar_xml_assinado(mdfe: Mdfe) -> str:
    if not mdfe.xml_assinado_path:
        raise ValueError("XML assinado não encontrado para este MDF-e.")

    caminho = Path(mdfe.xml_assinado_path)

    if not caminho.exists():
        raise ValueError("Arquivo XML assinado não encontrado no servidor.")

    parser = etree.XMLParser(
        remove_blank_text=True,
        remove_comments=True,
        resolve_entities=False,
    )

    raiz = etree.parse(str(caminho), parser).getroot()

    xml = etree.tostring(
        raiz,
        encoding="unicode",
        xml_declaration=False,
        pretty_print=False,
    )

    return xml.strip()


def _extrair_texto_por_tag(raiz, nome_tag: str) -> str | None:
    elementos = raiz.xpath(f"//*[local-name()='{nome_tag}']")
    if not elementos:
        return None

    texto = elementos[0].text
    return texto.strip() if texto else None


def _extrair_elemento_por_tag(raiz, nome_tag: str):
    elementos = raiz.xpath(f"//*[local-name()='{nome_tag}']")
    if not elementos:
        return None

    return elementos[0]


def _xml_do_elemento(elemento) -> str:
    return etree.tostring(
        elemento,
        encoding="unicode",
        xml_declaration=False,
        pretty_print=False,
    ).strip()


def _extrair_xml_retorno(resposta_texto: str) -> str:
    if not resposta_texto:
        return ""

    try:
        raiz_soap = etree.fromstring(resposta_texto.encode("utf-8"))

        resultado_base64 = _extrair_texto_por_tag(raiz_soap, "mdfeResultMsg")
        if resultado_base64:
            return _descompactar_base64(resultado_base64)

        mdfe_recepcao_result = _extrair_elemento_por_tag(
            raiz_soap,
            "mdfeRecepcaoResult",
        )

        if mdfe_recepcao_result is not None:
            ret_mdfe = _extrair_elemento_por_tag(
                mdfe_recepcao_result,
                "retMDFe",
            )

            if ret_mdfe is not None:
                return _xml_do_elemento(ret_mdfe)

            return _xml_do_elemento(mdfe_recepcao_result)

        ret_mdfe = _extrair_elemento_por_tag(raiz_soap, "retMDFe")
        if ret_mdfe is not None:
            return _xml_do_elemento(ret_mdfe)

        return resposta_texto

    except Exception:
        return resposta_texto


def _interpretar_retorno_sefaz(resposta_texto: str) -> dict:
    xml_retorno = _extrair_xml_retorno(resposta_texto)

    retorno = {
        "cStat": None,
        "xMotivo": None,
        "nRec": None,
        "protocolo": None,
        "xml_retorno": xml_retorno,
    }

    if not xml_retorno:
        retorno["xMotivo"] = "SEFAZ não retornou conteúdo."
        return retorno

    try:
        raiz = etree.fromstring(xml_retorno.encode("utf-8"))

        retorno["cStat"] = _extrair_texto_por_tag(raiz, "cStat")
        retorno["xMotivo"] = _extrair_texto_por_tag(raiz, "xMotivo")
        retorno["nRec"] = _extrair_texto_por_tag(raiz, "nRec")
        retorno["protocolo"] = _extrair_texto_por_tag(raiz, "nProt")

        return retorno

    except Exception:
        retorno["xMotivo"] = "Não foi possível interpretar o XML de retorno da SEFAZ."
        return retorno


def enviar_mdfe_homologacao(db: Session, mdfe_id: int) -> dict:
    mdfe = db.query(Mdfe).filter(Mdfe.id == mdfe_id).first()

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    certificado = obter_certificado_por_cnpj(
        db=db,
        cnpj_enviado=mdfe.empresa.cnpj,
    )

    if not certificado:
        raise ValueError("Certificado digital ativo não encontrado para a empresa.")

    caminho_pfx = Path(certificado.arquivo_path)

    if not caminho_pfx.exists():
        raise ValueError("Arquivo do certificado digital não encontrado.")

    senha = descriptografar_senha(certificado.senha_criptografada)

    xml_assinado = _carregar_xml_assinado(mdfe)

    dados_compactados_base64 = _compactar_base64(xml_assinado)
    envelope = _montar_envelope_recepcao(dados_compactados_base64)

    PASTA_DEBUG.mkdir(parents=True, exist_ok=True)

    (PASTA_DEBUG / "xml_compactado_origem_debug.xml").write_text(
        xml_assinado,
        encoding="utf-8",
    )

    (PASTA_DEBUG / "envelope_debug.xml").write_text(
        envelope,
        encoding="utf-8",
    )

    sessao = requests.Session()
    sessao.verify = False

    sessao.mount(
        "https://",
        Pkcs12Adapter(
            pkcs12_filename=str(caminho_pfx),
            pkcs12_password=senha,
        ),
    )

    headers = {
        "Content-Type": (
            f'application/soap+xml; charset=utf-8; action="{SOAP_ACTION_RECEPCAO}"'
        ),
    }

    resposta = sessao.post(
        URL_RECEPCAO_HOMOLOGACAO,
        data=envelope.encode("utf-8"),
        headers=headers,
        timeout=60,
    )

    resposta_texto = resposta.text or ""

    (PASTA_DEBUG / "resposta_debug.xml").write_text(
        resposta_texto,
        encoding="utf-8",
    )

    retorno_interpretado = _interpretar_retorno_sefaz(resposta_texto)

    (PASTA_DEBUG / "retorno_interpretado_debug.xml").write_text(
        retorno_interpretado.get("xml_retorno") or "",
        encoding="utf-8",
    )

    return {
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "headers": dict(resposta.headers),
        "resposta": resposta_texto,
        "envelope_enviado": envelope,
        "cStat": retorno_interpretado.get("cStat"),
        "xMotivo": retorno_interpretado.get("xMotivo"),
        "nRec": retorno_interpretado.get("nRec"),
        "protocolo": retorno_interpretado.get("protocolo"),
        "xml_retorno": retorno_interpretado.get("xml_retorno"),
    }