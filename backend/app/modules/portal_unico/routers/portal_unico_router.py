from fastapi import APIRouter, Depends, Form, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.portal_unico.services.consulta_cct_consumo_service import (
    listar_consumos_por_chave_cct,
)
from app.modules.portal_unico.services.consulta_cct_historico_service import (
    listar_consultas_cct,
    obter_consulta_cct,
)
from app.modules.portal_unico.services.consulta_cct_processamento_service import (
    criar_consulta_cct,
    processar_consulta_cct,
)
from app.modules.portal_unico.services.consulta_cct_saldo_service import (
    listar_opcoes_filtros_cct,
    listar_saldos_cct,
)

router = APIRouter(
    prefix="/exportacao/cct",
    tags=["Exportação"],
)


def _usuario_sessao(request: Request) -> dict:
    usuario = request.session.get("usuario_logado")
    return usuario if isinstance(usuario, dict) else {}


def _usuario_esta_logado(request: Request) -> bool:
    return bool(request.session.get("usuario_logado"))


def _limpar_filtro(valor: str | None) -> str | None:
    if not valor:
        return None

    valor = valor.strip()
    return valor or None


def _filtros_cct(
    numero_nfe: str | None = None,
    centro_origem: str | None = None,
    material: str | None = None,
    porto: str | None = None,
    recinto: str | None = None,
    situacao: str | None = None,
) -> dict:
    return {
        "numero_nfe": _limpar_filtro(numero_nfe),
        "centro_origem": _limpar_filtro(centro_origem),
        "material": _limpar_filtro(material),
        "porto": _limpar_filtro(porto),
        "recinto": _limpar_filtro(recinto),
        "situacao": _limpar_filtro(situacao),
    }


def _anexar_consumos_cct(
    db: Session,
    saldos_cct: list,
):
    for saldo in saldos_cct:
        saldo.consumos_cct = listar_consumos_por_chave_cct(
            db=db,
            chave=saldo.chave,
        )

    return saldos_cct


@router.get("/")
async def tela_consulta_cct(
    request: Request,
    numero_nfe: str | None = Query(default=None),
    centro_origem: str | None = Query(default=None),
    material: str | None = Query(default=None),
    porto: str | None = Query(default=None),
    recinto: str | None = Query(default=None),
    situacao: str | None = Query(default=None),
    db: Session = Depends(get_db),
):
    if not _usuario_esta_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    filtros = _filtros_cct(
        numero_nfe=numero_nfe,
        centro_origem=centro_origem,
        material=material,
        porto=porto,
        recinto=recinto,
        situacao=situacao,
    )

    saldos_cct = listar_saldos_cct(
        db=db,
        **filtros,
    )

    saldos_cct = _anexar_consumos_cct(
        db=db,
        saldos_cct=saldos_cct,
    )

    opcoes_filtros = listar_opcoes_filtros_cct(db=db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_cct.html",
        context={
            "page_title": "Estoque CCT - GrainDesk",
            "titulo_pagina": "Estoque CCT",
            "subtitulo_pagina": "Consulta automática de recepção e saldo das NF-es no Portal Único Siscomex CCT",
            "chaves": "",
            "resultados": [],
            "saldos_cct": saldos_cct,
            "opcoes_filtros": opcoes_filtros,
            "filtros": filtros,
            "mensagem": None,
            "erro": None,
            "modo_historico": False,
        },
    )


@router.post("/")
async def consultar_cct(
    request: Request,
    chaves: str = Form(...),
    db: Session = Depends(get_db),
):
    if not _usuario_esta_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    chaves_limpas = [
        "".join(filter(str.isdigit, linha))
        for linha in chaves.splitlines()
        if linha.strip()
    ]

    usuario = _usuario_sessao(request)

    try:
        consulta = criar_consulta_cct(
            db=db,
            chaves=chaves_limpas,
            usuario_id=usuario.get("id"),
            usuario_nome=usuario.get("nome"),
        )

        consulta = processar_consulta_cct(
            db=db,
            consulta_id=consulta.id,
            chaves=chaves_limpas,
        )

        resultados = getattr(consulta, "resultados_processados", [])

        quantidade_atualizada = len(
            [
                item
                for item in resultados
                if isinstance(item, dict) and item.get("chave")
            ]
        )

        mensagem = (
            "Consulta processada com sucesso. "
            f"{quantidade_atualizada} NF-e(s) atualizada(s) no Estoque CCT."
        )
        erro = None

    except Exception as exc:
        resultados = []
        mensagem = None
        erro = f"Erro ao consultar CCT: {exc}"

    filtros = _filtros_cct()

    saldos_cct = listar_saldos_cct(
        db=db,
        **filtros,
    )

    saldos_cct = _anexar_consumos_cct(
        db=db,
        saldos_cct=saldos_cct,
    )

    opcoes_filtros = listar_opcoes_filtros_cct(db=db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_cct.html",
        context={
            "page_title": "Estoque CCT - GrainDesk",
            "titulo_pagina": "Estoque CCT",
            "subtitulo_pagina": "Consulta automática de recepção e saldo das NF-es no Portal Único Siscomex CCT",
            "chaves": chaves,
            "resultados": resultados,
            "saldos_cct": saldos_cct,
            "opcoes_filtros": opcoes_filtros,
            "filtros": filtros,
            "mensagem": mensagem,
            "erro": erro,
            "modo_historico": False,
        },
    )


@router.get("/historico")
async def historico_consultas_cct(
    request: Request,
    db: Session = Depends(get_db),
):
    if not _usuario_esta_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    consultas = listar_consultas_cct(db=db, limite=100)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_cct_historico.html",
        context={
            "page_title": "Histórico CCT - GrainDesk",
            "titulo_pagina": "Histórico de Consultas CCT",
            "subtitulo_pagina": "Consultas realizadas no Portal Único CCT",
            "consultas": consultas,
        },
    )


@router.get("/historico/{consulta_id}")
async def detalhe_consulta_cct(
    consulta_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    if not _usuario_esta_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    consulta = obter_consulta_cct(db=db, consulta_id=consulta_id)

    if not consulta:
        return RedirectResponse(url="/exportacao/cct/historico", status_code=303)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_cct.html",
        context={
            "page_title": f"Consulta CCT #{consulta.id} - GrainDesk",
            "titulo_pagina": f"Consulta CCT #{consulta.id}",
            "subtitulo_pagina": "Resultado salvo da consulta CCT",
            "consulta": consulta,
            "resultados": consulta.itens,
            "saldos_cct": [],
            "opcoes_filtros": listar_opcoes_filtros_cct(db=db),
            "filtros": _filtros_cct(),
            "mensagem": consulta.mensagem,
            "erro": consulta.erro,
            "chaves": "",
            "modo_historico": True,
        },
    )