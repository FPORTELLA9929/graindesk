from fastapi import APIRouter, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo
from app.modules.exportacao.models.exportacao_re import ExportacaoRE


router = APIRouter(
    prefix="/exportacao",
    tags=["Exportação"],
)


@router.get("/")
async def dashboard_exportacao(
    request: Request,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    total_entradas = db.query(ExportacaoEntrada).count()
    total_saidas = db.query(ExportacaoSaida).count()
    total_consumos = db.query(ExportacaoConsumo).count()
    total_res = db.query(ExportacaoRE).count()

    saldo_original = (
        db.query(func.coalesce(func.sum(ExportacaoEntrada.quantidade_original), 0))
        .scalar()
        or 0
    )

    saldo_disponivel = (
        db.query(func.coalesce(func.sum(ExportacaoEntrada.quantidade_saldo), 0))
        .scalar()
        or 0
    )

    saldo_consumido = saldo_original - saldo_disponivel

    entradas_recentes = (
        db.query(ExportacaoEntrada)
        .order_by(ExportacaoEntrada.criado_em.desc())
        .limit(10)
        .all()
    )

    saidas_recentes = (
        db.query(ExportacaoSaida)
        .order_by(ExportacaoSaida.criado_em.desc())
        .limit(10)
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/dashboard.html",
        context={
            "page_title": "Controle de Exportação - GrainDesk",
            "titulo_pagina": "Controle de Exportação",
            "subtitulo_pagina": "Gestão de entradas equiparadas, exportações, RE, DUE e rastreabilidade",
            "total_entradas": total_entradas,
            "total_saidas": total_saidas,
            "total_consumos": total_consumos,
            "total_res": total_res,
            "saldo_original": saldo_original,
            "saldo_consumido": saldo_consumido,
            "saldo_disponivel": saldo_disponivel,
            "entradas_recentes": entradas_recentes,
            "saidas_recentes": saidas_recentes,
        },
    )