import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.empresa import EmpresaCreate, EmpresaUpdate
from app.services import empresa_service


router = APIRouter(tags=["Empresas"])


BASE_DIR = Path(__file__).resolve().parents[3]

STATIC_DIR = BASE_DIR / "frontend" / "static"
UPLOADS_DIR = STATIC_DIR / "uploads"
UPLOAD_DIR = UPLOADS_DIR / "empresas"

if UPLOADS_DIR.exists() and not UPLOADS_DIR.is_dir():
    UPLOADS_DIR.unlink()

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)


def salvar_logo_empresa(logo: UploadFile | None) -> str | None:
    if not logo or not logo.filename:
        return None

    extensao = Path(logo.filename).suffix.lower()

    if extensao not in [".png", ".jpg", ".jpeg", ".webp"]:
        raise HTTPException(
            status_code=400,
            detail="Formato de logo inválido. Use PNG, JPG, JPEG ou WEBP.",
        )

    nome_arquivo = f"{uuid.uuid4().hex}{extensao}"
    caminho_arquivo = UPLOAD_DIR / nome_arquivo

    with caminho_arquivo.open("wb") as buffer:
        shutil.copyfileobj(logo.file, buffer)

    return f"/static/uploads/empresas/{nome_arquivo}"


@router.get("/empresas/")
def redirecionar_empresas_antigo():
    return RedirectResponse(url="/cadastros/empresas/", status_code=303)


@router.get("/empresas/nova")
def redirecionar_nova_empresa_antigo():
    return RedirectResponse(url="/cadastros/empresas/nova", status_code=303)


@router.get("/empresas/novo")
def redirecionar_novo_empresa_antigo():
    return RedirectResponse(url="/cadastros/empresas/nova", status_code=303)


@router.get("/empresas/{empresa_id}/editar")
def redirecionar_editar_empresa_antigo(empresa_id: int):
    return RedirectResponse(url=f"/cadastros/empresas/{empresa_id}/editar", status_code=303)


@router.get("/cadastros/empresas/")
def listar_empresas(request: Request, db: Session = Depends(get_db)):
    empresas = empresa_service.listar_empresas(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/empresas.html",
        context={
            "empresas": empresas,
            "page_title": "Empresas - GrainDesk",
            "titulo_pagina": "Empresas",
            "subtitulo_pagina": "Cadastro de empresas vinculadas ao GrainDesk.",
        },
    )


@router.get("/cadastros/empresas/nova")
def nova_empresa(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/empresa_form.html",
        context={
            "empresa": None,
            "modo": "nova",
            "page_title": "Nova Empresa - GrainDesk",
            "titulo_pagina": "Nova Empresa",
            "subtitulo_pagina": "Inclua uma nova empresa no cadastro.",
        },
    )


@router.post("/cadastros/empresas/nova")
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
    logo: UploadFile | None = File(None),
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

    empresa = empresa_service.criar_empresa(db, dados)

    logo_path = salvar_logo_empresa(logo)

    if logo_path:
        empresa_service.atualizar_logo_empresa(db, empresa, logo_path)

    return RedirectResponse(url="/cadastros/empresas/", status_code=303)


@router.get("/cadastros/empresas/{empresa_id}/editar")
def editar_empresa(
    empresa_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
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
            "titulo_pagina": "Editar Empresa",
            "subtitulo_pagina": "Atualize os dados cadastrais da empresa.",
        },
    )


@router.post("/cadastros/empresas/{empresa_id}/editar")
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
    logo: UploadFile | None = File(None),
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

    logo_path = salvar_logo_empresa(logo)

    if logo_path:
        empresa_service.atualizar_logo_empresa(db, empresa, logo_path)

    return RedirectResponse(url="/cadastros/empresas/", status_code=303)


@router.post("/cadastros/empresas/{empresa_id}/excluir")
def excluir_empresa(
    empresa_id: int,
    db: Session = Depends(get_db),
):
    empresa = empresa_service.buscar_empresa(db, empresa_id)

    if not empresa:
        raise HTTPException(status_code=404, detail="Empresa não encontrada.")

    empresa_service.excluir_empresa(db, empresa)

    return RedirectResponse(url="/cadastros/empresas/", status_code=303)