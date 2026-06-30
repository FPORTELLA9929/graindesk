from datetime import datetime

from sqlalchemy.orm import Session

from app.modules.portal_unico.models.portal_unico_cct_saldo import (
    PortalUnicoCCTSaldo,
)
from app.modules.portal_unico.models.portal_unico_consulta_cct import (
    PortalUnicoConsultaCCT,
)
from app.modules.portal_unico.models.portal_unico_consulta_cct_item import (
    PortalUnicoConsultaCCTItem,
)
from app.modules.portal_unico.services.consulta_cct_service import (
    consultar_notas_cct,
)


def criar_consulta_cct(
    db: Session,
    chaves: list[str],
    usuario_id: int | None = None,
    usuario_nome: str | None = None,
):
    consulta = PortalUnicoConsultaCCT(
        usuario_id=usuario_id,
        usuario_nome=usuario_nome,
        status="pendente",
        quantidade_chaves=len(chaves),
        mensagem="Consulta criada e aguardando processamento.",
    )

    db.add(consulta)
    db.commit()
    db.refresh(consulta)

    return consulta


def atualizar_saldo_cct(
    db: Session,
    item: dict,
):
    chave = item.get("chave")

    if not chave:
        return None

    saldo = (
        db.query(PortalUnicoCCTSaldo)
        .filter(PortalUnicoCCTSaldo.chave == chave)
        .first()
    )

    if not saldo:
        saldo = PortalUnicoCCTSaldo(
            chave=chave,
        )
        db.add(saldo)

    saldo.numero_nfe = item.get("numero_nfe")
    saldo.centro_origem = item.get("centro_origem")
    saldo.material = item.get("material")
    saldo.peso_nf = item.get("peso_nf") or 0
    saldo.peso_cct = item.get("peso_cct") or 0
    saldo.saldo = item.get("saldo") or 0
    saldo.porto = item.get("porto")
    saldo.recinto = item.get("recinto")
    saldo.situacao = item.get("situacao")
    saldo.mensagem = item.get("mensagem")
    saldo.json_retorno = item.get("dados")

    return saldo


def processar_consulta_cct(
    db: Session,
    consulta_id: int,
    chaves: list[str],
):
    consulta = (
        db.query(PortalUnicoConsultaCCT)
        .filter(PortalUnicoConsultaCCT.id == consulta_id)
        .first()
    )

    if not consulta:
        raise ValueError("Consulta CCT não encontrada.")

    consulta.status = "processando"
    consulta.iniciado_em = datetime.utcnow()
    consulta.mensagem = "Consulta em processamento."
    db.commit()

    try:
        resultados = consultar_notas_cct(
            db=db,
            chaves=chaves,
        )

        if resultados is None:
            resultados = []

        if isinstance(resultados, dict):
            resultados = [resultados]

        if isinstance(resultados, bool):
            resultados = [
                {
                    "chave": "",
                    "numero_nfe": None,
                    "centro_origem": None,
                    "material": None,
                    "peso_nf": 0,
                    "peso_cct": 0,
                    "saldo": 0,
                    "porto": None,
                    "recinto": None,
                    "situacao": "Erro",
                    "mensagem": f"Retorno inválido da consulta CCT: {resultados}",
                    "dados": {"retorno": resultados},
                }
            ]

        quantidade_ok = 0
        quantidade_invalidas = 0
        quantidade_nao_encontradas = 0

        for item in resultados:
            if not isinstance(item, dict):
                item = {
                    "chave": "",
                    "numero_nfe": None,
                    "centro_origem": None,
                    "material": None,
                    "peso_nf": 0,
                    "peso_cct": 0,
                    "saldo": 0,
                    "porto": None,
                    "recinto": None,
                    "situacao": "Erro",
                    "mensagem": f"Retorno inválido da consulta CCT: {item}",
                    "dados": {"retorno": str(item)},
                }

            situacao = item.get("situacao") or "Erro"

            if situacao == "OK":
                quantidade_ok += 1
            elif situacao == "Inválida":
                quantidade_invalidas += 1
            else:
                quantidade_nao_encontradas += 1

            consulta_item = PortalUnicoConsultaCCTItem(
                consulta_id=consulta.id,
                chave=item.get("chave") or "",
                numero_nfe=item.get("numero_nfe"),
                centro_origem=item.get("centro_origem"),
                material=item.get("material"),
                peso_nf=item.get("peso_nf") or 0,
                peso_cct=item.get("peso_cct") or 0,
                saldo=item.get("saldo") or 0,
                porto=item.get("porto"),
                recinto=item.get("recinto"),
                situacao=situacao,
                mensagem=item.get("mensagem"),
                json_retorno=item.get("dados"),
            )

            db.add(consulta_item)

            atualizar_saldo_cct(
                db=db,
                item=item,
            )

        consulta.status = "concluida"
        consulta.quantidade_ok = quantidade_ok
        consulta.quantidade_invalidas = quantidade_invalidas
        consulta.quantidade_nao_encontradas = quantidade_nao_encontradas
        consulta.finalizado_em = datetime.utcnow()
        consulta.mensagem = "Consulta processada com sucesso."
        consulta.erro = None

        db.commit()
        db.refresh(consulta)

        consulta.resultados_processados = resultados

        return consulta

    except Exception as exc:
        consulta.status = "erro"
        consulta.erro = str(exc)
        consulta.mensagem = "Erro ao processar consulta CCT."
        consulta.finalizado_em = datetime.utcnow()

        db.commit()
        db.refresh(consulta)

        consulta.resultados_processados = []

        return consulta