from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.schemas.tipo_veiculo import (
    TipoVeiculoCreate,
    TipoVeiculoUpdate,
)
from app.modules.cadastros.services import tipo_veiculo_service


router = APIRouter(prefix="/cadastros/tipos-veiculo", tags=["Tipos de Veículo"])


def decimal_ou_none(valor: str | None):
    if not valor:
        return None

    try:
        return Decimal(valor.replace(",", "."))
    except InvalidOperation:
        return None


@router.get("/")
def listar_tipos_veiculo(
    request: Request,
    descricao: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1),
    db: Session = Depends(get_db),
):
    resultado = tipo_veiculo_service.listar_tipos_veiculo(
        db=db,
        descricao=descricao,
        status=status,
        page=page,
        per_page=25,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/tipos_veiculo.html",
        context={
            "tipos_veiculo": resultado["items"],
            "total": resultado["total"],
            "page": resultado["page"],
            "per_page": resultado["per_page"],
            "total_pages": resultado["total_pages"],
            "filtro_descricao": descricao or "",
            "filtro_status": status or "",
            "page_title": "Tipos de Veículo - GrainDesk",
            "titulo_pagina": "Tipos de Veículo",
            "subtitulo_pagina": "Cadastro de tipos de veículo para logística e frete.",
        },
    )


@router.get("/novo")
def novo_tipo_veiculo(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/tipo_veiculo_form.html",
        context={
            "tipo_veiculo": None,
            "modo": "novo",
            "page_title": "Novo Tipo de Veículo - GrainDesk",
            "titulo_pagina": "Novo Tipo de Veículo",
            "subtitulo_pagina": "Inclua um novo tipo de veículo no cadastro.",
        },
    )


@router.post("/novo")
def criar_tipo_veiculo(
    descricao: str = Form(...),
    quantidade_eixos: int = Form(...),
    quantidade_placas: int = Form(...),
    capacidade_kg: str | None = Form(None),
    capacidade_m3: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    if quantidade_eixos <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantidade de eixos deve ser maior que zero.",
        )

    if quantidade_placas <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantidade de placas deve ser maior que zero.",
        )

    if tipo_veiculo_service.buscar_por_descricao(db, descricao):
        raise HTTPException(
            status_code=400,
            detail="Já existe tipo de veículo cadastrado com esta descrição.",
        )

    dados = TipoVeiculoCreate(
        descricao=descricao.strip(),
        quantidade_eixos=quantidade_eixos,
        quantidade_placas=quantidade_placas,
        capacidade_kg=decimal_ou_none(capacidade_kg),
        capacidade_m3=decimal_ou_none(capacidade_m3),
        ativo=ativo,
    )

    tipo_veiculo_service.criar_tipo_veiculo(db, dados)

    return RedirectResponse(url="/cadastros/tipos-veiculo/", status_code=303)


@router.get("/{tipo_veiculo_id}/editar")
def editar_tipo_veiculo(
    tipo_veiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    tipo_veiculo = tipo_veiculo_service.buscar_tipo_veiculo(db, tipo_veiculo_id)

    if not tipo_veiculo:
        raise HTTPException(status_code=404, detail="Tipo de veículo não encontrado.")

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/tipo_veiculo_form.html",
        context={
            "tipo_veiculo": tipo_veiculo,
            "modo": "editar",
            "page_title": "Editar Tipo de Veículo - GrainDesk",
            "titulo_pagina": "Editar Tipo de Veículo",
            "subtitulo_pagina": "Atualize os dados do tipo de veículo.",
        },
    )


@router.post("/{tipo_veiculo_id}/editar")
def atualizar_tipo_veiculo(
    tipo_veiculo_id: int,
    descricao: str = Form(...),
    quantidade_eixos: int = Form(...),
    quantidade_placas: int = Form(...),
    capacidade_kg: str | None = Form(None),
    capacidade_m3: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    tipo_veiculo = tipo_veiculo_service.buscar_tipo_veiculo(db, tipo_veiculo_id)

    if not tipo_veiculo:
        raise HTTPException(status_code=404, detail="Tipo de veículo não encontrado.")

    if quantidade_eixos <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantidade de eixos deve ser maior que zero.",
        )

    if quantidade_placas <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantidade de placas deve ser maior que zero.",
        )

    existente = tipo_veiculo_service.buscar_por_descricao(db, descricao)

    if existente and existente.id != tipo_veiculo_id:
        raise HTTPException(
            status_code=400,
            detail="Já existe outro tipo de veículo cadastrado com esta descrição.",
        )

    dados = TipoVeiculoUpdate(
        descricao=descricao.strip(),
        quantidade_eixos=quantidade_eixos,
        quantidade_placas=quantidade_placas,
        capacidade_kg=decimal_ou_none(capacidade_kg),
        capacidade_m3=decimal_ou_none(capacidade_m3),
        ativo=ativo,
    )

    tipo_veiculo_service.atualizar_tipo_veiculo(db, tipo_veiculo, dados)

    return RedirectResponse(url="/cadastros/tipos-veiculo/", status_code=303)


@router.post("/{tipo_veiculo_id}/excluir")
def excluir_tipo_veiculo(
    tipo_veiculo_id: int,
    db: Session = Depends(get_db),
):
    tipo_veiculo = tipo_veiculo_service.buscar_tipo_veiculo(db, tipo_veiculo_id)

    if not tipo_veiculo:
        raise HTTPException(status_code=404, detail="Tipo de veículo não encontrado.")

    tipo_veiculo_service.excluir_tipo_veiculo(db, tipo_veiculo)

    return RedirectResponse(url="/cadastros/tipos-veiculo/", status_code=303)