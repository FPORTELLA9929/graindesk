import os
import re
import shutil
from pathlib import Path

from cryptography import x509
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.serialization import pkcs12
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.modules.admin.models.certificado_digital import CertificadoDigital
from app.modules.cadastros.models.empresa import Empresa


UPLOAD_DIR = Path("static/uploads/certificados")
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def apenas_numeros(valor: str | None) -> str:
    if not valor:
        return ""

    return re.sub(r"\D", "", valor)


def get_fernet() -> Fernet:
    chave = os.getenv("CERT_SECRET_KEY")

    if not chave:
        raise ValueError(
            "CERT_SECRET_KEY não configurada no .env. "
            "Crie uma chave Fernet para criptografar senhas dos certificados."
        )

    return Fernet(chave.encode())


def criptografar_senha(senha: str) -> str:
    fernet = get_fernet()
    return fernet.encrypt(senha.encode()).decode()


def descriptografar_senha(senha_criptografada: str) -> str:
    fernet = get_fernet()
    return fernet.decrypt(senha_criptografada.encode()).decode()


def validar_extensao_certificado(filename: str):
    extensao = Path(filename).suffix.lower()

    if extensao not in [".pfx", ".p12"]:
        raise ValueError("O certificado precisa ser um arquivo .pfx ou .p12.")


def obter_atributo_nome(name: x509.Name, oid: x509.ObjectIdentifier) -> str | None:
    try:
        atributos = name.get_attributes_for_oid(oid)

        if not atributos:
            return None

        return atributos[0].value
    except Exception:
        return None


def extrair_cnpj_do_certificado(certificado: x509.Certificate) -> str:
    """
    Em muitos certificados e-CNPJ, o CNPJ aparece no subject como parte do commonName:
    EXEMPLO: EMPRESA LTDA:12345678000199

    Também pode aparecer em outros campos. Por segurança, procuramos qualquer sequência
    de 14 dígitos dentro do subject.
    """

    subject_texto = certificado.subject.rfc4514_string()
    issuer_texto = certificado.issuer.rfc4514_string()

    texto_busca = f"{subject_texto} {issuer_texto}"
    encontrados = re.findall(r"\d{14}", texto_busca)

    if encontrados:
        return encontrados[0]

    return ""


def extrair_razao_social_do_certificado(certificado: x509.Certificate) -> str | None:
    common_name = obter_atributo_nome(
        certificado.subject,
        x509.NameOID.COMMON_NAME,
    )

    if not common_name:
        return None

    if ":" in common_name:
        return common_name.split(":")[0].strip()

    return common_name.strip()


def extrair_emissor_do_certificado(certificado: x509.Certificate) -> str | None:
    common_name = obter_atributo_nome(
        certificado.issuer,
        x509.NameOID.COMMON_NAME,
    )

    if common_name:
        return common_name.strip()

    organization = obter_atributo_nome(
        certificado.issuer,
        x509.NameOID.ORGANIZATION_NAME,
    )

    if organization:
        return organization.strip()

    return certificado.issuer.rfc4514_string()


def ler_dados_certificado_pfx(
    caminho_arquivo: Path,
    senha: str,
) -> dict:
    try:
        conteudo = caminho_arquivo.read_bytes()

        chave_privada, certificado, certificados_adicionais = pkcs12.load_key_and_certificates(
            conteudo,
            senha.encode(),
        )

        if not certificado:
            raise ValueError("Não foi possível localizar o certificado dentro do arquivo.")

        cnpj_certificado = extrair_cnpj_do_certificado(certificado)

        return {
            "cnpj_certificado_extraido": cnpj_certificado,
            "razao_social_certificado": extrair_razao_social_do_certificado(certificado),
            "serial_number": str(certificado.serial_number),
            "emissor": extrair_emissor_do_certificado(certificado),
            "data_emissao": certificado.not_valid_before_utc.date(),
            "data_validade": certificado.not_valid_after_utc.date(),
        }

    except ValueError as erro:
        raise erro

    except Exception:
        raise ValueError(
            "Não foi possível abrir o certificado. "
            "Verifique se o arquivo é válido e se a senha está correta."
        )


def listar_certificados(db: Session):
    return (
        db.query(CertificadoDigital)
        .join(Empresa, CertificadoDigital.empresa_id == Empresa.id)
        .order_by(CertificadoDigital.id.desc())
        .all()
    )


def buscar_certificado(db: Session, certificado_id: int):
    return (
        db.query(CertificadoDigital)
        .filter(CertificadoDigital.id == certificado_id)
        .first()
    )


def criar_certificado(
    db: Session,
    empresa_id: int,
    arquivo: UploadFile,
    senha: str,
    tipo_certificado: str = "A1",
    ativo: bool = True,
):
    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()

    if not empresa:
        raise ValueError("Empresa não encontrada.")

    cnpj_empresa = apenas_numeros(empresa.cnpj)

    if len(cnpj_empresa) != 14:
        raise ValueError("O CNPJ da empresa cadastrada é inválido.")

    cnpj_raiz_empresa = cnpj_empresa[:8]

    if not arquivo or not arquivo.filename:
        raise ValueError("Arquivo do certificado não enviado.")

    validar_extensao_certificado(arquivo.filename)

    nome_arquivo_seguro = re.sub(r"[^a-zA-Z0-9_.-]", "_", arquivo.filename)
    nome_arquivo = f"{cnpj_empresa}_{nome_arquivo_seguro}"
    caminho_arquivo = UPLOAD_DIR / nome_arquivo

    try:
        with caminho_arquivo.open("wb") as buffer:
            shutil.copyfileobj(arquivo.file, buffer)

        dados_certificado = ler_dados_certificado_pfx(
            caminho_arquivo=caminho_arquivo,
            senha=senha,
        )

        cnpj_extraido = apenas_numeros(
            dados_certificado.get("cnpj_certificado_extraido")
        )

        if cnpj_extraido and cnpj_extraido[:8] != cnpj_raiz_empresa:
            raise ValueError(
                "O CNPJ do certificado não pertence à mesma raiz do CNPJ da empresa selecionada."
            )

        # Regra: apenas 1 certificado ativo por raiz de CNPJ.
        if ativo:
            certificados_ativos_mesma_raiz = (
                db.query(CertificadoDigital)
                .filter(CertificadoDigital.cnpj_raiz == cnpj_raiz_empresa)
                .filter(CertificadoDigital.ativo == True)
                .all()
            )

            for cert in certificados_ativos_mesma_raiz:
                cert.ativo = False

        certificado = CertificadoDigital(
            empresa_id=empresa.id,
            cnpj_certificado=cnpj_extraido or cnpj_empresa,
            cnpj_raiz=cnpj_raiz_empresa,
            razao_social_certificado=dados_certificado.get("razao_social_certificado"),
            serial_number=dados_certificado.get("serial_number"),
            emissor=dados_certificado.get("emissor"),
            data_emissao=dados_certificado.get("data_emissao"),
            data_validade=dados_certificado.get("data_validade"),
            arquivo_path=str(caminho_arquivo),
            senha_criptografada=criptografar_senha(senha),
            tipo_certificado=tipo_certificado or "A1",
            ativo=ativo,
        )

        db.add(certificado)
        db.commit()
        db.refresh(certificado)

        return certificado

    except Exception as erro:
        if caminho_arquivo.exists():
            caminho_arquivo.unlink()

        db.rollback()

        if isinstance(erro, ValueError):
            raise erro

        raise ValueError("Erro ao cadastrar certificado digital.")


def atualizar_certificado(
    db: Session,
    certificado_id: int,
    ativo: bool,
    tipo_certificado: str = "A1",
    senha: str | None = None,
):
    certificado = buscar_certificado(db, certificado_id)

    if not certificado:
        raise ValueError("Certificado não encontrado.")

    certificado.tipo_certificado = tipo_certificado or "A1"
    certificado.ativo = ativo

    if senha:
        certificado.senha_criptografada = criptografar_senha(senha)

    # Se ativar este certificado, desativa os outros da mesma raiz.
    if ativo:
        outros_certificados = (
            db.query(CertificadoDigital)
            .filter(CertificadoDigital.cnpj_raiz == certificado.cnpj_raiz)
            .filter(CertificadoDigital.id != certificado.id)
            .filter(CertificadoDigital.ativo == True)
            .all()
        )

        for cert in outros_certificados:
            cert.ativo = False

    db.commit()
    db.refresh(certificado)

    return certificado


def excluir_certificado(db: Session, certificado_id: int):
    certificado = buscar_certificado(db, certificado_id)

    if not certificado:
        raise ValueError("Certificado não encontrado.")

    if certificado.arquivo_path and os.path.exists(certificado.arquivo_path):
        os.remove(certificado.arquivo_path)

    db.delete(certificado)
    db.commit()

    return True


def obter_certificado_por_cnpj(db: Session, cnpj_enviado: str):
    cnpj_limpo = apenas_numeros(cnpj_enviado)

    if len(cnpj_limpo) != 14:
        return None

    cnpj_raiz = cnpj_limpo[:8]

    return (
        db.query(CertificadoDigital)
        .filter(CertificadoDigital.cnpj_raiz == cnpj_raiz)
        .filter(CertificadoDigital.ativo == True)
        .order_by(CertificadoDigital.id.desc())
        .first()
    )