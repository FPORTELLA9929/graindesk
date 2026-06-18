from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.permissoes import redirecionar_se_nao_logado_ou_sem_permissao
from app.database.session import get_db
from app.modules.admin.services import usuario_service


router = APIRouter(prefix="/admin/usuarios", tags=["Admin - Usuários"])


@router.get("/")
async def listar_usuarios(
    request: Request,
    db: Session = Depends(get_db),
    busca: str | None = Query(default=None),
    status: str | None = Query(default=None),
    perfil: str | None = Query(default=None),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    usuarios = usuario_service.listar_usuarios(db)

    if busca:
        termo = busca.lower().strip()
        usuarios = [
            usuario for usuario in usuarios
            if termo in usuario.nome.lower()
            or termo in usuario.email.lower()
            or termo in usuario.empresa.lower()
        ]

    if status:
        usuarios = [
            usuario for usuario in usuarios
            if usuario.status == status
        ]

    if perfil:
        usuarios = [
            usuario for usuario in usuarios
            if usuario.perfil == perfil
        ]

    total_usuarios = len(usuarios)
    total_ativos = len([u for u in usuarios if u.status == "ativo"])
    total_pendentes = len([u for u in usuarios if u.status == "pendente"])
    total_inativos = len([u for u in usuarios if u.status in ["inativo", "recusado"]])

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/usuarios.html",
        context={
            "page_title": "Administração de Usuários - GrainDesk",
            "titulo_pagina": "Administração de Usuários",
            "subtitulo_pagina": "Aprovação, inativação e gestão de acesso dos usuários.",
            "usuarios": usuarios,
            "total_usuarios": total_usuarios,
            "total_ativos": total_ativos,
            "total_pendentes": total_pendentes,
            "total_inativos": total_inativos,
            "filtro_busca": busca or "",
            "filtro_status": status or "",
            "filtro_perfil": perfil or "",
        },
    )


@router.post("/{usuario_id}/aprovar")
async def aprovar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    usuario = usuario_service.buscar_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    usuario_service.aprovar_usuario(db, usuario)

    return RedirectResponse(url="/admin/usuarios/", status_code=303)


@router.post("/{usuario_id}/recusar")
async def recusar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    usuario = usuario_service.buscar_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    usuario_service.recusar_usuario(db, usuario)

    return RedirectResponse(url="/admin/usuarios/", status_code=303)


@router.post("/{usuario_id}/inativar")
async def inativar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    usuario = usuario_service.buscar_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if usuario.id == request.session.get("usuario_id"):
        return RedirectResponse(url="/admin/usuarios/", status_code=303)

    usuario_service.inativar_usuario(db, usuario)

    return RedirectResponse(url="/admin/usuarios/", status_code=303)


@router.post("/{usuario_id}/reativar")
async def reativar_usuario(
    usuario_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    usuario = usuario_service.buscar_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    usuario_service.reativar_usuario(db, usuario)

    return RedirectResponse(url="/admin/usuarios/", status_code=303)


@router.post("/{usuario_id}/alterar-perfil")
async def alterar_perfil_usuario(
    usuario_id: int,
    request: Request,
    perfil: str = Form(...),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="usuarios",
    )
    if redirect:
        return redirect

    if perfil not in ["administrador", "operacional"]:
        return RedirectResponse(url="/admin/usuarios/", status_code=303)

    usuario = usuario_service.buscar_usuario_por_id(db, usuario_id)

    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    if usuario.id == request.session.get("usuario_id") and perfil != "administrador":
        return RedirectResponse(url="/admin/usuarios/", status_code=303)

    usuario.perfil = perfil
    db.commit()
    db.refresh(usuario)

    return RedirectResponse(url="/admin/usuarios/", status_code=303)