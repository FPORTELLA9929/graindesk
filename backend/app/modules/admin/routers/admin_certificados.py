from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.permissoes import redirecionar_se_nao_logado_ou_sem_permissao
from app.database.session import get_db
from app.modules.cadastros.models.empresa import Empresa
from app.modules.admin.services import certificado_digital_service


router = APIRouter(
    prefix="/admin/certificados",
    tags=["Admin - Certificados Digitais"],
)


@router.get("/")
async def listar_certificados(
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="certificados",
    )
    if redirect:
        return redirect

    certificados = certificado_digital_service.listar_certificados(db)

    empresas = (
        db.query(Empresa)
        .filter(Empresa.ativo == True)
        .order_by(Empresa.razao_social.asc())
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/certificados.html",
        context={
            "page_title": "Certificados Digitais - GrainDesk",
            "titulo_pagina": "Certificados Digitais",
            "subtitulo_pagina": "Gestão de certificados A1 por empresa e raiz de CNPJ.",
            "certificados": certificados,
            "empresas": empresas,
            "erro": None,
        },
    )


@router.post("/novo")
async def criar_certificado(
    request: Request,
    empresa_id: int = Form(...),
    senha: str = Form(...),
    tipo_certificado: str = Form(default="A1"),
    ativo: bool = Form(default=False),
    arquivo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="certificados",
    )
    if redirect:
        return redirect

    try:
        certificado_digital_service.criar_certificado(
            db=db,
            empresa_id=empresa_id,
            arquivo=arquivo,
            senha=senha,
            tipo_certificado=tipo_certificado,
            ativo=ativo,
        )
    except ValueError as erro:
        certificados = certificado_digital_service.listar_certificados(db)

        empresas = (
            db.query(Empresa)
            .filter(Empresa.ativo == True)
            .order_by(Empresa.razao_social.asc())
            .all()
        )

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="admin/certificados.html",
            context={
                "page_title": "Certificados Digitais - GrainDesk",
                "titulo_pagina": "Certificados Digitais",
                "subtitulo_pagina": "Gestão de certificados A1 por empresa e raiz de CNPJ.",
                "certificados": certificados,
                "empresas": empresas,
                "erro": str(erro),
            },
        )

    return RedirectResponse(url="/admin/certificados/", status_code=303)


@router.post("/{certificado_id}/ativar")
async def ativar_certificado(
    certificado_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="certificados",
    )
    if redirect:
        return redirect

    certificado = certificado_digital_service.buscar_certificado(db, certificado_id)

    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado.")

    certificado_digital_service.atualizar_certificado(
        db=db,
        certificado_id=certificado_id,
        ativo=True,
        tipo_certificado=certificado.tipo_certificado,
    )

    return RedirectResponse(url="/admin/certificados/", status_code=303)


@router.post("/{certificado_id}/inativar")
async def inativar_certificado(
    certificado_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="certificados",
    )
    if redirect:
        return redirect

    certificado = certificado_digital_service.buscar_certificado(db, certificado_id)

    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado.")

    certificado_digital_service.atualizar_certificado(
        db=db,
        certificado_id=certificado_id,
        ativo=False,
        tipo_certificado=certificado.tipo_certificado,
    )

    return RedirectResponse(url="/admin/certificados/", status_code=303)


@router.post("/{certificado_id}/excluir")
async def excluir_certificado(
    certificado_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="certificados",
    )
    if redirect:
        return redirect

    certificado = certificado_digital_service.buscar_certificado(db, certificado_id)

    if not certificado:
        raise HTTPException(status_code=404, detail="Certificado não encontrado.")

    certificado_digital_service.excluir_certificado(db, certificado_id)

    return RedirectResponse(url="/admin/certificados/", status_code=303)