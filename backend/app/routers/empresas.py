from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.services import empresa_service


router = APIRouter(prefix="/empresas", tags=["Empresas"])


@router.get("/")
def listar_empresas(request: Request, db: Session = Depends(get_db)):
    empresas = empresa_service.listar_empresas(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/empresas.html",
        context={
            "empresas": empresas,
            "page_title": "Empresas - GrainDesk",
        },
    )


@router.get("/nova")
def nova_empresa(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/empresa_form.html",
        context={
            "empresa": None,
            "modo": "nova",
            "page_title": "Nova Empresa - GrainDesk",
        },
    )


@router.post("/nova")
def criar_empresa(
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cnpj: str = Form(...),
    inscricao_estadual: str | None = Form(None),
    logradouro: str | None = Form(None),
    numero: str | None = Form(None),
    bairro: str | None = Form(None),
    cidade: str | None = Form(None),
    estado: str | None = Form(None),
    cep: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    if empresa_service.buscar_por_cnpj(db, cnpj):
        raise HTTPException(status_code=400, detail="Já existe empresa cadastrada com este CNPJ.")

    dados = EmpresaCreate(
        razao_social=razao_social,
        nome_fantasia=nome_fantasia,
        cnpj=cnpj,
        inscricao_estadual=inscricao_estadual,
        logradouro=logradouro,
        numero=numero,
        bairro=bairro,
        cidade=cidade,
        estado=estado,
        cep=cep,
        telefone=telefone,
        email=email,
        ativo=ativo,
    )

    empresa_service.criar_empresa(db, dados)
    return RedirectResponse(url="/empresas/", status_code=303)


@router.get("/{empresa_id}/editar")
def editar_empresa(empresa_id: int, request: Request, db: Session = Depends(get_db)):
    empresa = empresa_service.buscar_empresa(db, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/empresa_form.html",
        context={
            "empresa": empresa,
            "modo": "editar",
            "page_title": "Editar Empresa - GrainDesk",
        },
    )


@router.post("/{empresa_id}/editar")
def atualizar_empresa(
    empresa_id: int,
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cnpj: str = Form(...),
    inscricao_estadual: str | None = Form(None),
    logradouro: str | None = Form(None),
    numero: str | None = Form(None),
    bairro: str | None = Form(None),
    cidade: str | None = Form(None),
    estado: str | None = Form(None),
    cep: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    empresa = empresa_service.buscar_empresa(db, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    dados = EmpresaUpdate(
        razao_social=razao_social,
        nome_fantasia=nome_fantasia,
        cnpj=cnpj,
        inscricao_estadual=inscricao_estadual,
        logradouro=logradouro,
        numero=numero,
        bairro=bairro,
        cidade=cidade,
        estado=estado,
        cep=cep,
        telefone=telefone,
        email=email,
        ativo=ativo,
    )

    empresa_service.atualizar_empresa(db, empresa, dados)
    return RedirectResponse(url="/empresas/", status_code=303)


@router.post("/{empresa_id}/excluir")
def excluir_empresa(empresa_id: int, db: Session = Depends(get_db)):
    empresa = empresa_service.buscar_empresa(db, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    empresa_service.excluir_empresa(db, empresa)
    return RedirectResponse(url="/empresas/", status_code=303)