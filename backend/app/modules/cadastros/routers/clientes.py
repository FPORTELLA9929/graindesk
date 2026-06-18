from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.cliente import ClienteCreate, ClienteUpdate
from app.modules.cadastros.services import cliente_service


router = APIRouter(tags=["Clientes"])


@router.get("/cadastros/clientes/")
def listar_clientes(request: Request, db: Session = Depends(get_db)):
    clientes = cliente_service.listar_clientes(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/clientes.html",
        context={
            "clientes": clientes,
            "page_title": "Clientes - GrainDesk",
            "titulo_pagina": "Clientes",
            "subtitulo_pagina": "Cadastro de clientes vinculados ao GrainDesk.",
        },
    )


@router.get("/cadastros/clientes/novo")
def novo_cliente(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/cliente_form.html",
        context={
            "cliente": None,
            "modo": "novo",
            "page_title": "Novo Cliente - GrainDesk",
            "titulo_pagina": "Novo Cliente",
            "subtitulo_pagina": "Inclua um novo cliente no cadastro.",
        },
    )


@router.post("/cadastros/clientes/novo")
def criar_cliente(
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
    if cliente_service.buscar_por_cpf_cnpj(db, cpf_cnpj):
        raise HTTPException(status_code=400, detail="Já existe cliente cadastrado com este CPF/CNPJ.")

    dados = ClienteCreate(
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

    cliente_service.criar_cliente(db, dados)

    return RedirectResponse(url="/cadastros/clientes/", status_code=303)


@router.get("/cadastros/clientes/{cliente_id}/editar")
def editar_cliente(
    cliente_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    cliente = cliente_service.buscar_cliente(db, cliente_id)

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/cliente_form.html",
        context={
            "cliente": cliente,
            "modo": "editar",
            "page_title": "Editar Cliente - GrainDesk",
            "titulo_pagina": "Editar Cliente",
            "subtitulo_pagina": "Atualize os dados cadastrais do cliente.",
        },
    )


@router.post("/cadastros/clientes/{cliente_id}/editar")
def atualizar_cliente(
    cliente_id: int,
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
    cliente = cliente_service.buscar_cliente(db, cliente_id)

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    dados = ClienteUpdate(
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

    cliente_service.atualizar_cliente(db, cliente, dados)

    return RedirectResponse(url="/cadastros/clientes/", status_code=303)


@router.post("/cadastros/clientes/{cliente_id}/excluir")
def excluir_cliente(
    cliente_id: int,
    db: Session = Depends(get_db),
):
    cliente = cliente_service.buscar_cliente(db, cliente_id)

    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente não encontrado.")

    cliente_service.excluir_cliente(db, cliente)

    return RedirectResponse(url="/cadastros/clientes/", status_code=303)