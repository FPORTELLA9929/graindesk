from sqlalchemy.orm import Session

from app.modules.mdfe.services import mdfe_service
from app.modules.mdfe.services import mdfe_xml_gerador_service
from app.modules.mdfe.services import mdfe_assinador_service
from app.modules.mdfe.services import mdfe_validador_xsd_service
from app.modules.mdfe.services import mdfe_sefaz_service


def _resumir_resposta_sefaz(resposta: str) -> str:
    if not resposta:
        return "SEFAZ não retornou conteúdo."

    resposta_limpa = " ".join(resposta.split())

    if len(resposta_limpa) > 1000:
        return resposta_limpa[:1000] + "..."

    return resposta_limpa


def emitir_mdfe(db: Session, mdfe_id: int) -> dict:
    mdfe = mdfe_service.buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    if mdfe.status not in ["rascunho", "erro", "validado"]:
        raise ValueError(
            "Somente MDF-e em rascunho, erro ou validado pode ser emitido."
        )

    try:
        mdfe_service.garantir_chave_mdfe(db, mdfe_id)

        mdfe_xml_gerador_service.gerar_xml_mdfe(
            db=db,
            mdfe_id=mdfe_id,
        )

        mdfe_assinador_service.assinar_xml_mdfe(
            db=db,
            mdfe_id=mdfe_id,
        )

        validacao = mdfe_validador_xsd_service.validar_xml_mdfe(mdfe_id)

        if not validacao.get("valido"):
            erros = validacao.get("erros", [])
            mensagem = "Erro na validação XSD do XML."

            if erros:
                mensagem = erros[0].get("mensagem") or mensagem

            mdfe_service.atualizar_retorno_sefaz(
                db=db,
                mdfe_id=mdfe_id,
                status="erro",
                mensagem_retorno=mensagem,
            )

            return {
                "sucesso": False,
                "status": "erro",
                "mensagem": mensagem,
                "validacao": validacao,
            }

        retorno_sefaz = mdfe_sefaz_service.enviar_mdfe_homologacao(
            db=db,
            mdfe_id=mdfe_id,
        )

        status_code = retorno_sefaz.get("status_code")
        resposta = retorno_sefaz.get("resposta") or ""
        mensagem_retorno = _resumir_resposta_sefaz(resposta)

        if status_code != 200:
            mensagem = (
                f"Erro HTTP ao enviar MDF-e para SEFAZ. "
                f"Status: {status_code}. Retorno: {mensagem_retorno}"
            )

            mdfe_service.atualizar_retorno_sefaz(
                db=db,
                mdfe_id=mdfe_id,
                status="erro",
                mensagem_retorno=mensagem,
            )

            return {
                "sucesso": False,
                "status": "erro",
                "mensagem": mensagem,
                "validacao": validacao,
                "sefaz": retorno_sefaz,
            }

        mdfe_service.atualizar_retorno_sefaz(
            db=db,
            mdfe_id=mdfe_id,
            status="enviado",
            mensagem_retorno=mensagem_retorno,
        )

        return {
            "sucesso": True,
            "status": "enviado",
            "mensagem": "MDF-e enviado para homologação SEFAZ. Verifique o retorno armazenado.",
            "validacao": validacao,
            "sefaz": retorno_sefaz,
        }

    except ValueError as erro:
        mdfe_service.atualizar_retorno_sefaz(
            db=db,
            mdfe_id=mdfe_id,
            status="erro",
            mensagem_retorno=str(erro),
        )

        return {
            "sucesso": False,
            "status": "erro",
            "mensagem": str(erro),
        }

    except Exception as erro:
        mdfe_service.atualizar_retorno_sefaz(
            db=db,
            mdfe_id=mdfe_id,
            status="erro",
            mensagem_retorno=f"Erro inesperado ao emitir MDF-e: {erro}",
        )

        return {
            "sucesso": False,
            "status": "erro",
            "mensagem": f"Erro inesperado ao emitir MDF-e: {erro}",
        }