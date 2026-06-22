from pathlib import Path

from cryptography.hazmat.primitives.serialization import (
    pkcs12,
    Encoding,
    PrivateFormat,
    NoEncryption,
)
from lxml import etree
from signxml import XMLSigner, methods
from signxml.algorithms import SignatureMethod, DigestAlgorithm
from sqlalchemy.orm import Session

from app.modules.admin.services.certificado_digital_service import (
    descriptografar_senha,
    obter_certificado_por_cnpj,
)
from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.services import mdfe_xml_gerador_service


PASTA_XML_ASSINADOS = Path("app/modules/mdfe/xml/assinados")
NAMESPACE_MDFE = "http://www.portalfiscal.inf.br/mdfe"


class AssinadorXMLComSHA1(XMLSigner):
    def check_deprecated_methods(self):
        return None


def _carregar_chave_e_certificado_pfx(caminho_pfx: Path, senha: str):
    conteudo = caminho_pfx.read_bytes()

    chave_privada, certificado, certificados_adicionais = (
        pkcs12.load_key_and_certificates(
            conteudo,
            senha.encode(),
        )
    )

    if not chave_privada:
        raise ValueError("Não foi possível carregar a chave privada do certificado.")

    if not certificado:
        raise ValueError("Não foi possível carregar o certificado digital.")

    chave_pem = chave_privada.private_bytes(
        Encoding.PEM,
        PrivateFormat.PKCS8,
        NoEncryption(),
    )

    certificado_pem = certificado.public_bytes(Encoding.PEM)

    return chave_pem, certificado_pem


def assinar_xml_mdfe(db: Session, mdfe_id: int) -> str:
    mdfe = db.query(Mdfe).filter(Mdfe.id == mdfe_id).first()

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    certificado = obter_certificado_por_cnpj(
        db=db,
        cnpj_enviado=mdfe.empresa.cnpj,
    )

    if not certificado:
        raise ValueError(
            "Nenhum certificado digital ativo encontrado para a empresa do MDF-e."
        )

    caminho_pfx = Path(certificado.arquivo_path)

    if not caminho_pfx.exists():
        raise ValueError("Arquivo do certificado digital não encontrado.")

    senha = descriptografar_senha(certificado.senha_criptografada)

    chave_pem, certificado_pem = _carregar_chave_e_certificado_pfx(
        caminho_pfx=caminho_pfx,
        senha=senha,
    )

    xml_nao_assinado = mdfe_xml_gerador_service.gerar_xml_mdfe(
        db=db,
        mdfe_id=mdfe_id,
    )

    parser = etree.XMLParser(remove_blank_text=True)
    raiz = etree.fromstring(xml_nao_assinado.encode("utf-8"), parser=parser)

    inf_mdfe = raiz.find(f".//{{{NAMESPACE_MDFE}}}infMDFe")

    if inf_mdfe is None:
        raise ValueError("Tag infMDFe não encontrada no XML.")

    id_inf_mdfe = inf_mdfe.get("Id")

    if not id_inf_mdfe:
        raise ValueError("A tag infMDFe não possui atributo Id.")

    assinador = AssinadorXMLComSHA1(
        method=methods.enveloped,
        signature_algorithm=SignatureMethod.RSA_SHA1,
        digest_algorithm=DigestAlgorithm.SHA1,
        c14n_algorithm="http://www.w3.org/TR/2001/REC-xml-c14n-20010315",
    )

    xml_assinado = assinador.sign(
        raiz,
        key=chave_pem,
        cert=certificado_pem,
        reference_uri=f"#{id_inf_mdfe}",
        always_add_key_value=False,
    )

    xml_string = etree.tostring(
        xml_assinado,
        encoding="utf-8",
        xml_declaration=True,
        pretty_print=True,
    ).decode("utf-8")

    PASTA_XML_ASSINADOS.mkdir(parents=True, exist_ok=True)

    caminho_xml_assinado = PASTA_XML_ASSINADOS / f"mdfe_{mdfe.id}_assinado.xml"

    caminho_xml_assinado.write_text(xml_string, encoding="utf-8")

    mdfe.xml_assinado_path = str(caminho_xml_assinado)
    db.commit()
    db.refresh(mdfe)

    return xml_string