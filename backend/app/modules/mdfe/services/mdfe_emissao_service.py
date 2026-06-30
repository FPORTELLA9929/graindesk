from sqlalchemy.orm import Session

from app.modules.mdfe.services import mdfe_service
from app.modules.mdfe.services import mdfe_xml_gerador_service
from app.modules.mdfe.services import mdfe_assinador_service
from app.modules.mdfe.services import mdfe_validador_xsd_service
from app.modules.mdfe.services import mdfe_sefaz_service


STATUS_SEFAZ = {
    "100": "autorizado",
    "101": "cancelado",
    "103": "lote_recebido",
    "104": "lote_processado",
    "105": "processando",
}


STATUS_REENVIAVEIS = [
    "rascunho",
    "erro",
    "validado",
    "enviado",
    "rejeitado",
    "lote_recebido",
    "lote_processado",
    "processando",
]


def _resumir_resposta_sefaz(resposta: str) -> str:
    if not resposta:
        return "SEFAZ não retornou conteúdo."

    resposta_limpa = " ".join(resposta.split())

    if len(resposta_limpa) > 1000:
        return resposta_limpa[:1000] + "..."

    return resposta_limpa


def _montar_mensagem_retorno(retorno_sefaz: dict) -> str:
    cstat = retorno_sefaz.get("cStat")
    motivo = retorno_sefaz.get("xMotivo")
    recibo = retorno_sefaz.get("nRec")
    protocolo = retorno_sefaz.get("protocolo")

    partes = []

    if cstat:
        partes.append(f"cStat: {cstat}")

    if motivo:
        partes.append(f"xMotivo: {motivo}")

    if recibo:
        partes.append(f"nRec: {recibo}")

    if protocolo:
        partes.append(f"Protocolo: {protocolo}")

    if partes:
        return " | ".join(partes)

    return _resumir_resposta_sefaz(retorno_sefaz.get("resposta") or "")


def _definir_status_por_retorno(retorno_sefaz: dict) -> str:
    cstat = retorno_sefaz.get("cStat")

    if not cstat:
        return "erro"

    return STATUS_SEFAZ.get(str(cstat), "rejeitado")


def emitir_mdfe(db: Session, mdfe_id: int) -> dict:
    mdfe = mdfe_service.buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    if mdfe.status not in STATUS_REENVIAVEIS:
        raise ValueError(
            "Somente MDF-e em rascunho, erro, validado, enviado, rejeitado ou em processamento pode ser emitido."
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

        if status_code != 200:
            mensagem = (
                f"Erro HTTP ao enviar MDF-e para SEFAZ. "
                f"Status: {status_code}. "
                f"Retorno: {_resumir_resposta_sefaz(retorno_sefaz.get('resposta') or '')}"
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

        status_final = _definir_status_por_retorno(retorno_sefaz)
        mensagem_retorno = _montar_mensagem_retorno(retorno_sefaz)

        mdfe_service.atualizar_retorno_sefaz(
            db=db,
            mdfe_id=mdfe_id,
            status=status_final,
            mensagem_retorno=mensagem_retorno,
            protocolo=retorno_sefaz.get("protocolo"),
            recibo=retorno_sefaz.get("nRec"),
            xml_retorno=retorno_sefaz.get("xml_retorno"),
        )

        sucesso = status_final in [
            "autorizado",
            "lote_recebido",
            "lote_processado",
            "processando",
        ]

        return {
            "sucesso": sucesso,
            "status": status_final,
            "mensagem": mensagem_retorno,
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