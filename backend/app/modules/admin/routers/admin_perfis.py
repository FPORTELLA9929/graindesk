from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.permissoes import redirecionar_se_nao_logado_ou_sem_permissao
from app.database.session import get_db
from app.modules.admin.services import perfil_service


router = APIRouter(prefix="/admin/perfis", tags=["Admin - Perfis"])


@router.get("/")
async def listar_perfis(
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="perfis",
    )
    if redirect:
        return redirect

    perfil_service.criar_perfis_padrao(db)
    perfil_service.criar_permissoes_padrao(db)

    perfis = perfil_service.listar_perfis(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/perfis.html",
        context={
            "page_title": "Perfis e Permissões - GrainDesk",
            "titulo_pagina": "Perfis e Permissões",
            "subtitulo_pagina": "Gerencie acessos por perfil de usuário.",
            "perfis": perfis,
        },
    )


@router.get("/{perfil_id}/permissoes")
async def editar_permissoes(
    perfil_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="perfis",
    )
    if redirect:
        return redirect

    perfil = perfil_service.buscar_perfil(db, perfil_id)

    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    permissoes = perfil_service.listar_permissoes(db)
    permissoes_marcadas = perfil_service.listar_permissoes_perfil(db, perfil_id)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/perfil_permissoes.html",
        context={
            "page_title": "Permissões do Perfil - GrainDesk",
            "titulo_pagina": f"Permissões - {perfil.nome}",
            "subtitulo_pagina": "Configure quais módulos este perfil poderá acessar.",
            "perfil": perfil,
            "permissoes": permissoes,
            "permissoes_marcadas": permissoes_marcadas,
        },
    )


@router.post("/{perfil_id}/permissoes")
async def salvar_permissoes(
    perfil_id: int,
    request: Request,
    permissoes: list[int] = Form(default=[]),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="perfis",
    )
    if redirect:
        return redirect

    perfil = perfil_service.buscar_perfil(db, perfil_id)

    if not perfil:
        raise HTTPException(status_code=404, detail="Perfil não encontrado.")

    perfil_service.atualizar_permissoes_perfil(
        db=db,
        perfil_id=perfil_id,
        permissoes_ids=permissoes,
    )

    return RedirectResponse(
        url="/admin/perfis/",
        status_code=303,
    )