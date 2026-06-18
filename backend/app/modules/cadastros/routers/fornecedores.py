from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.fornecedor import FornecedorCreate, FornecedorUpdate
from app.modules.cadastros.services import fornecedor_service


router = APIRouter(tags=["Fornecedores"])


@router.get("/cadastros/fornecedores/")
def listar_fornecedores(request: Request, db: Session = Depends(get_db)):
    fornecedores = fornecedor_service.listar_fornecedores(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/fornecedores.html",
        context={
            "fornecedores": fornecedores,
            "page_title": "Fornecedores - GrainDesk",
            "titulo_pagina": "Fornecedores",
            "subtitulo_pagina": "Cadastro de fornecedores vinculados ao GrainDesk.",
        },
    )


@router.get("/cadastros/fornecedores/novo")
def novo_fornecedor(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/fornecedor_form.html",
        context={
            "fornecedor": None,
            "modo": "novo",
            "page_title": "Novo Fornecedor - GrainDesk",
            "titulo_pagina": "Novo Fornecedor",
            "subtitulo_pagina": "Inclua um novo fornecedor no cadastro.",
        },
    )


@router.post("/cadastros/fornecedores/novo")
def criar_fornecedor(
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cpf_cnpj: str = Form(...),
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
    if fornecedor_service.buscar_por_cpf_cnpj(db, cpf_cnpj):
        raise HTTPException(status_code=400, detail="Já existe fornecedor cadastrado com este CPF/CNPJ.")

    dados = FornecedorCreate(
        razao_social=razao_social,
        nome_fantasia=nome_fantasia,
        cpf_cnpj=cpf_cnpj,
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

    fornecedor_service.criar_fornecedor(db, dados)

    return RedirectResponse(url="/cadastros/fornecedores/", status_code=303)


@router.get("/cadastros/fornecedores/{fornecedor_id}/editar")
def editar_fornecedor(
    fornecedor_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    fornecedor = fornecedor_service.buscar_fornecedor(db, fornecedor_id)

    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/fornecedor_form.html",
        context={
            "fornecedor": fornecedor,
            "modo": "editar",
            "page_title": "Editar Fornecedor - GrainDesk",
            "titulo_pagina": "Editar Fornecedor",
            "subtitulo_pagina": "Atualize os dados cadastrais do fornecedor.",
        },
    )


@router.post("/cadastros/fornecedores/{fornecedor_id}/editar")
def atualizar_fornecedor(
    fornecedor_id: int,
    razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cpf_cnpj: str = Form(...),
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
    fornecedor = fornecedor_service.buscar_fornecedor(db, fornecedor_id)

    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")

    dados = FornecedorUpdate(
        razao_social=razao_social,
        nome_fantasia=nome_fantasia,
        cpf_cnpj=cpf_cnpj,
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

    fornecedor_service.atualizar_fornecedor(db, fornecedor, dados)

    return RedirectResponse(url="/cadastros/fornecedores/", status_code=303)


@router.post("/cadastros/fornecedores/{fornecedor_id}/excluir")
def excluir_fornecedor(
    fornecedor_id: int,
    db: Session = Depends(get_db),
):
    fornecedor = fornecedor_service.buscar_fornecedor(db, fornecedor_id)

    if not fornecedor:
        raise HTTPException(status_code=404, detail="Fornecedor não encontrado.")

    fornecedor_service.excluir_fornecedor(db, fornecedor)

    return RedirectResponse(url="/cadastros/fornecedores/", status_code=303)