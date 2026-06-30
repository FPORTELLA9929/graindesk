from pathlib import Path

import requests
from requests_pkcs12 import Pkcs12Adapter
from sqlalchemy.orm import Session

from app.modules.admin.services.certificado_digital_service import (
    descriptografar_senha,
    obter_certificado_por_cnpj,
)
from app.modules.cadastros.models.empresa import Empresa


URL_NFE_CONSULTA_HOMOLOGACAO = (
    "https://homologacao.nfe.fazenda.gov.br/NFeConsultaProtocolo4/NFeConsultaProtocolo4.asmx"
)

SOAP_ACTION_NFE_CONSULTA = (
    "http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4/nfeConsultaNF"
)


def montar_consulta_nfe(chave_acesso: str) -> str:
    return f"""<consSitNFe xmlns="http://www.portalfiscal.inf.br/nfe" versao="4.00">
    <tpAmb>2</tpAmb>
    <xServ>CONSULTAR</xServ>
    <chNFe>{chave_acesso}</chNFe>
</consSitNFe>"""


def montar_envelope_consulta_nfe(xml_consulta: str) -> str:
    return f"""<?xml version="1.0" encoding="utf-8"?>
<soap:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"
               xmlns:xsd="http://www.w3.org/2001/XMLSchema"
               xmlns:soap="http://schemas.xmlsoap.org/soap/envelope/">
    <soap:Body>
        <nfeDadosMsg xmlns="http://www.portalfiscal.inf.br/nfe/wsdl/NFeConsultaProtocolo4">
            {xml_consulta}
        </nfeDadosMsg>
    </soap:Body>
</soap:Envelope>"""


def consultar_nfe_sefaz_homologacao(
    db: Session,
    empresa_id: int,
    chave_acesso: str,
) -> dict:
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()

    if not empresa:
        raise ValueError("Empresa selecionada não encontrada.")

    certificado = obter_certificado_por_cnpj(
        db=db,
        cnpj_enviado=empresa.cnpj,
    )

    if not certificado:
        raise ValueError("Certificado digital ativo não encontrado para a empresa.")

    caminho_pfx = Path(certificado.arquivo_path)

    if not caminho_pfx.exists():
        raise ValueError("Arquivo do certificado digital não encontrado.")

    senha = descriptografar_senha(certificado.senha_criptografada)

    xml_consulta = montar_consulta_nfe(chave_acesso)
    envelope = montar_envelope_consulta_nfe(xml_consulta)

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
        "SOAPAction": SOAP_ACTION_NFE_CONSULTA,
    }

    resposta = sessao.post(
        URL_NFE_CONSULTA_HOMOLOGACAO,
        data=envelope.encode("utf-8"),
        headers=headers,
        timeout=60,
    )

    return {
        "status_code": resposta.status_code,
        "reason": resposta.reason,
        "resposta": resposta.text,
        "envelope_enviado": envelope,
    }