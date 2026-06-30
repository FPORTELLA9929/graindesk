from dataclasses import dataclass

from sqlalchemy.orm import Session

from app.modules.admin.services.certificado_digital_service import (
    obter_certificado_por_cnpj,
)
from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.services.nfe_consulta_protocolo_service import (
    consultar_nfe_sefaz_homologacao,
)


@dataclass
class ResultadoAverbacao:
    chave: str
    numero_due: str | None
    item_nfe: str | None
    item_due: str | None
    quantidade_averbada: str | None
    data_averbacao: str | None
    situacao: str


def validar_chave_nfe(chave: str) -> bool:
    chave_limpa = "".join(filter(str.isdigit, chave))
    return len(chave_limpa) == 44


def consultar_averbacao_sefaz_por_chave(
    db: Session,
    chave: str,
    empresa_id: int,
) -> ResultadoAverbacao:
    chave_limpa = "".join(filter(str.isdigit, chave))

    if not validar_chave_nfe(chave_limpa):
        return ResultadoAverbacao(
            chave=chave,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao="Chave inválida. A chave NF-e deve ter 44 dígitos.",
        )

    empresa = db.query(Empresa).filter(Empresa.id == empresa_id).first()

    if not empresa:
        return ResultadoAverbacao(
            chave=chave_limpa,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao="Empresa selecionada não encontrada.",
        )

    certificado = obter_certificado_por_cnpj(
        db=db,
        cnpj_enviado=empresa.cnpj,
    )

    if not certificado:
        return ResultadoAverbacao(
            chave=chave_limpa,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao="Nenhum certificado digital ativo encontrado para a raiz do CNPJ da empresa selecionada.",
        )

    if certificado.vencido:
        return ResultadoAverbacao(
            chave=chave_limpa,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao="Certificado digital encontrado, porém está vencido.",
        )

    try:
        resposta = consultar_nfe_sefaz_homologacao(
            db=db,
            empresa_id=empresa_id,
            chave_acesso=chave_limpa,
        )

        return ResultadoAverbacao(
            chave=chave_limpa,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao=f"Consulta SEFAZ executada. HTTP {resposta['status_code']} - {resposta['reason']}",
        )

    except Exception as erro:
        return ResultadoAverbacao(
            chave=chave_limpa,
            numero_due=None,
            item_nfe=None,
            item_due=None,
            quantidade_averbada=None,
            data_averbacao=None,
            situacao=f"Erro ao consultar SEFAZ: {erro}",
        )