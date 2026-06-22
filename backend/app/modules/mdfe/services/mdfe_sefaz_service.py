from pathlib import Path

import requests
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


def _remover_declaracao_xml(xml: str) -> str:
    xml = xml.replace('<?xml version="1.0" encoding="utf-8"?>', "")
    xml = xml.replace('<?xml version="1.0" encoding="UTF-8"?>', "")
    xml = xml.replace('<?xml version="1.0"?>', "")
    return xml.strip()


def _montar_xml_lote(xml_mdfe_assinado: str, id_lote: str) -> str:
    return f"""<enviMDFe xmlns="http://www.portalfiscal.inf.br/mdfe" versao="3.00">
<idLote>{id_lote}</idLote>
{xml_mdfe_assinado}
</enviMDFe>"""


def _montar_envelope_recepcao(xml_lote: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <mdfeRecepcao xmlns="http://www.portalfiscal.inf.br/mdfe/wsdl/MDFeRecepcaoSinc">
            <mdfeDadosMsg><![CDATA[{xml_lote}]]></mdfeDadosMsg>
        </mdfeRecepcao>
    </soap:Body>
</soap:Envelope>"""


def _carregar_xml_assinado(mdfe: Mdfe) -> str:
    if not mdfe.xml_assinado_path:
        raise ValueError("XML assinado não encontrado para este MDF-e.")

    caminho = Path(mdfe.xml_assinado_path)

    if not caminho.exists():
        raise ValueError("Arquivo XML assinado não encontrado no servidor.")

    xml = caminho.read_text(encoding="utf-8")
    return _remover_declaracao_xml(xml)


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

    id_lote = str(mdfe.id).zfill(15)

    xml_lote = _montar_xml_lote(
        xml_mdfe_assinado=xml_assinado,
        id_lote=id_lote,
    )

    envelope = _montar_envelope_recepcao(xml_lote)

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
        "Content-Type": "text/xml; charset=utf-8",
        "SOAPAction": SOAP_ACTION_RECEPCAO,
    }

    resposta = sessao.post(
        URL_RECEPCAO_HOMOLOGACAO,
        data=envelope.encode("utf-8"),
        headers=headers,
        timeout=60,
    )

    return {
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "headers": dict(resposta.headers),
        "resposta": resposta.text,
        "envelope_enviado": envelope,
    }