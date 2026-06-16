from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.municipio import Municipio
from app.schemas.transportador import TransportadorCreate, TransportadorUpdate
from app.services import transportador_service


router = APIRouter(prefix="/cadastros/transportadores", tags=["Transportadores"])


def buscar_municipio_por_id(db: Session, municipio_id: int | None):
    if not municipio_id:
        return None

    return (
        db.query(Municipio)
        .filter(Municipio.codigo_ibge == municipio_id)
        .first()
    )


@router.get("/")
def listar_transportadores(
    request: Request,
    busca: str | None = Query(None),
    tipo_pessoa: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1),
    db: Session = Depends(get_db),
):
    resultado = transportador_service.listar_transportadores(
        db=db,
        busca=busca,
        tipo_pessoa=tipo_pessoa,
        status=status,
        page=page,
        per_page=25,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/transportadores.html",
        context={
            "transportadores": resultado["items"],
            "total": resultado["total"],
            "page": resultado["page"],
            "per_page": resultado["per_page"],
            "total_pages": resultado["total_pages"],
            "filtro_busca": busca or "",
            "filtro_tipo_pessoa": tipo_pessoa or "",
            "filtro_status": status or "",
            "page_title": "Transportadores - GrainDesk",
            "titulo_pagina": "Transportadores",
            "subtitulo_pagina": "Cadastro de pessoas físicas e jurídicas que realizam transporte.",
        },
    )


@router.get("/novo")
def novo_transportador(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/transportador_form.html",
        context={
            "transportador": None,
            "municipio": None,
            "modo": "novo",
            "page_title": "Novo Transportador - GrainDesk",
            "titulo_pagina": "Novo Transportador",
            "subtitulo_pagina": "Inclua um novo transportador no cadastro.",
        },
    )


@router.post("/novo")
def criar_transportador(
    tipo_pessoa: str = Form(...),
    nome_razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cpf_cnpj: str = Form(...),
    rg_ie: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    municipio_id: int = Form(...),
    endereco: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    if tipo_pessoa not in ["PF", "PJ"]:
        raise HTTPException(status_code=400, detail="Tipo de pessoa inválido.")

    municipio = buscar_municipio_por_id(db, municipio_id)

    if not municipio:
        raise HTTPException(status_code=400, detail="Município inválido.")

    if transportador_service.buscar_por_cpf_cnpj(db, cpf_cnpj):
        raise HTTPException(
            status_code=400,
            detail="Já existe transportador cadastrado com este CPF/CNPJ.",
        )

    dados = TransportadorCreate(
        tipo_pessoa=tipo_pessoa,
        nome_razao_social=nome_razao_social.strip(),
        nome_fantasia=nome_fantasia.strip() if nome_fantasia else None,
        cpf_cnpj=cpf_cnpj.strip(),
        rg_ie=rg_ie.strip() if rg_ie else None,
        telefone=telefone.strip() if telefone else None,
        email=email.strip() if email else None,
        municipio_id=municipio_id,
        endereco=endereco.strip() if endereco else None,
        ativo=ativo,
    )

    transportador_service.criar_transportador(db, dados)

    return RedirectResponse(url="/cadastros/transportadores/", status_code=303)


@router.get("/{transportador_id}/editar")
def editar_transportador(
    transportador_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    transportador = transportador_service.buscar_transportador(db, transportador_id)

    if not transportador:
        raise HTTPException(status_code=404, detail="Transportador não encontrado.")

    municipio = buscar_municipio_por_id(db, transportador.municipio_id)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/transportador_form.html",
        context={
            "transportador": transportador,
            "municipio": municipio,
            "modo": "editar",
            "page_title": "Editar Transportador - GrainDesk",
            "titulo_pagina": "Editar Transportador",
            "subtitulo_pagina": "Atualize os dados cadastrais do transportador.",
        },
    )


@router.post("/{transportador_id}/editar")
def atualizar_transportador(
    transportador_id: int,
    tipo_pessoa: str = Form(...),
    nome_razao_social: str = Form(...),
    nome_fantasia: str | None = Form(None),
    cpf_cnpj: str = Form(...),
    rg_ie: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    municipio_id: int = Form(...),
    endereco: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    transportador = transportador_service.buscar_transportador(db, transportador_id)

    if not transportador:
        raise HTTPException(status_code=404, detail="Transportador não encontrado.")

    if tipo_pessoa not in ["PF", "PJ"]:
        raise HTTPException(status_code=400, detail="Tipo de pessoa inválido.")

    municipio = buscar_municipio_por_id(db, municipio_id)

    if not municipio:
        raise HTTPException(status_code=400, detail="Município inválido.")

    existente = transportador_service.buscar_por_cpf_cnpj(db, cpf_cnpj)

    if existente and existente.id != transportador_id:
        raise HTTPException(
            status_code=400,
            detail="Já existe outro transportador cadastrado com este CPF/CNPJ.",
        )

    dados = TransportadorUpdate(
        tipo_pessoa=tipo_pessoa,
        nome_razao_social=nome_razao_social.strip(),
        nome_fantasia=nome_fantasia.strip() if nome_fantasia else None,
        cpf_cnpj=cpf_cnpj.strip(),
        rg_ie=rg_ie.strip() if rg_ie else None,
        telefone=telefone.strip() if telefone else None,
        email=email.strip() if email else None,
        municipio_id=municipio_id,
        endereco=endereco.strip() if endereco else None,
        ativo=ativo,
    )

    transportador_service.atualizar_transportador(db, transportador, dados)

    return RedirectResponse(url="/cadastros/transportadores/", status_code=303)


@router.post("/{transportador_id}/excluir")
def excluir_transportador(
    transportador_id: int,
    db: Session = Depends(get_db),
):
    transportador = transportador_service.buscar_transportador(db, transportador_id)

    if not transportador:
        raise HTTPException(status_code=404, detail="Transportador não encontrado.")

    transportador_service.excluir_transportador(db, transportador)

    return RedirectResponse(url="/cadastros/transportadores/", status_code=303)