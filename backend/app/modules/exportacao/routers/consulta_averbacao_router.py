from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.services.consulta_averbacao_service import (
    consultar_averbacoes_por_chaves,
)

router = APIRouter(
    prefix="/exportacao/averbacao",
    tags=["Exportação"],
)


def listar_empresas_ativas(db: Session):
    return (
        db.query(Empresa)
        .filter(Empresa.ativo == True)
        .order_by(Empresa.razao_social.asc())
        .all()
    )


@router.get("/")
async def tela_consulta_averbacao(
    request: Request,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    empresas = listar_empresas_ativas(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_averbacao.html",
        context={
            "page_title": "Consulta Averbação - GrainDesk",
            "titulo_pagina": "Consulta Averbação",
            "subtitulo_pagina": "Consulta do evento 790700 - Averbação para Exportação",
            "empresas": empresas,
            "empresa_id": "",
            "chaves": "",
            "resultados": [],
        },
    )


@router.post("/")
async def consultar_averbacao(
    request: Request,
    empresa_id: int = Form(...),
    chaves: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    empresas = listar_empresas_ativas(db)

    lista_chaves = [
        chave.strip()
        for chave in chaves.replace(",", "\n").splitlines()
        if chave.strip()
    ]

    resultados = consultar_averbacoes_por_chaves(
        db=db,
        chaves=lista_chaves,
        empresa_id=empresa_id,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_averbacao.html",
        context={
            "page_title": "Consulta Averbação - GrainDesk",
            "titulo_pagina": "Consulta Averbação",
            "subtitulo_pagina": "Consulta do evento 790700 - Averbação para Exportação",
            "empresas": empresas,
            "empresa_id": empresa_id,
            "chaves": chaves,
            "resultados": resultados,
        },
    )