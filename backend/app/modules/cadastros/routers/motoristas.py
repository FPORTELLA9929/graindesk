import re
from datetime import date

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.models.transportador import Transportador
from app.modules.cadastros.schemas.motorista import (
    MotoristaCreate,
    MotoristaUpdate,
)
from app.modules.cadastros.services import motorista_service


router = APIRouter(prefix="/cadastros/motoristas", tags=["Motoristas"])


def somente_numeros(valor: str | None):
    if not valor:
        return None

    return re.sub(r"\D", "", valor)


def date_ou_none(valor: str | None):
    if not valor:
        return None

    return date.fromisoformat(valor)


def listar_transportadores_ativos(db: Session):
    return (
        db.query(Transportador)
        .filter(Transportador.ativo == True)
        .order_by(Transportador.nome_razao_social.asc())
        .all()
    )


@router.get("/")
def listar_motoristas(
    request: Request,
    busca: str | None = Query(None),
    transportador_id: int | None = Query(None),
    status: str | None = Query(None),
    db: Session = Depends(get_db),
):
    motoristas = motorista_service.listar_motoristas(
        db=db,
        busca=busca,
        transportador_id=transportador_id,
        status=status,
    )

    transportadores = listar_transportadores_ativos(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/motoristas.html",
        context={
            "motoristas": motoristas,
            "transportadores": transportadores,
            "filtro_busca": busca or "",
            "filtro_transportador_id": transportador_id or "",
            "filtro_status": status or "",
            "page_title": "Motoristas - GrainDesk",
            "titulo_pagina": "Motoristas",
            "subtitulo_pagina": "Cadastro de motoristas vinculados aos transportadores.",
        },
    )


@router.get("/novo")
def novo_motorista(request: Request, db: Session = Depends(get_db)):
    transportadores = listar_transportadores_ativos(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/motorista_form.html",
        context={
            "motorista": None,
            "transportadores": transportadores,
            "modo": "novo",
            "page_title": "Novo Motorista - GrainDesk",
            "titulo_pagina": "Novo Motorista",
            "subtitulo_pagina": "Inclua um novo motorista no cadastro.",
        },
    )


@router.post("/novo")
def criar_motorista(
    nome: str = Form(...),
    cpf: str = Form(...),
    rg: str | None = Form(None),
    cnh: str = Form(...),
    categoria_cnh: str | None = Form(None),
    validade_cnh: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    transportador_id: int | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    cpf_limpo = somente_numeros(cpf)

    if not cpf_limpo or len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido.")

    if not cnh or not cnh.strip():
        raise HTTPException(status_code=400, detail="CNH é obrigatória.")

    if motorista_service.buscar_por_cpf(db, cpf_limpo):
        raise HTTPException(
            status_code=400,
            detail="Já existe motorista cadastrado com este CPF.",
        )

    dados = MotoristaCreate(
        nome=nome.strip(),
        cpf=cpf_limpo,
        rg=rg.strip() if rg else None,
        cnh=cnh.strip(),
        categoria_cnh=categoria_cnh.strip() if categoria_cnh else None,
        validade_cnh=date_ou_none(validade_cnh),
        telefone=telefone.strip() if telefone else None,
        email=email.strip() if email else None,
        transportador_id=transportador_id,
        ativo=ativo,
    )

    motorista_service.criar_motorista(db, dados)

    return RedirectResponse(url="/cadastros/motoristas/", status_code=303)


@router.get("/{motorista_id}/editar")
def editar_motorista(
    motorista_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    motorista = motorista_service.buscar_motorista(db, motorista_id)

    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado.")

    transportadores = listar_transportadores_ativos(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/motorista_form.html",
        context={
            "motorista": motorista,
            "transportadores": transportadores,
            "modo": "editar",
            "page_title": "Editar Motorista - GrainDesk",
            "titulo_pagina": "Editar Motorista",
            "subtitulo_pagina": "Atualize os dados cadastrais do motorista.",
        },
    )


@router.post("/{motorista_id}/editar")
def atualizar_motorista(
    motorista_id: int,
    nome: str = Form(...),
    cpf: str = Form(...),
    rg: str | None = Form(None),
    cnh: str = Form(...),
    categoria_cnh: str | None = Form(None),
    validade_cnh: str | None = Form(None),
    telefone: str | None = Form(None),
    email: str | None = Form(None),
    transportador_id: int | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    motorista = motorista_service.buscar_motorista(db, motorista_id)

    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado.")

    cpf_limpo = somente_numeros(cpf)

    if not cpf_limpo or len(cpf_limpo) != 11:
        raise HTTPException(status_code=400, detail="CPF inválido.")

    if not cnh or not cnh.strip():
        raise HTTPException(status_code=400, detail="CNH é obrigatória.")

    existente = motorista_service.buscar_por_cpf(db, cpf_limpo)

    if existente and existente.id != motorista_id:
        raise HTTPException(
            status_code=400,
            detail="Já existe outro motorista cadastrado com este CPF.",
        )

    dados = MotoristaUpdate(
        nome=nome.strip(),
        cpf=cpf_limpo,
        rg=rg.strip() if rg else None,
        cnh=cnh.strip(),
        categoria_cnh=categoria_cnh.strip() if categoria_cnh else None,
        validade_cnh=date_ou_none(validade_cnh),
        telefone=telefone.strip() if telefone else None,
        email=email.strip() if email else None,
        transportador_id=transportador_id,
        ativo=ativo,
    )

    motorista_service.atualizar_motorista(db, motorista, dados)

    return RedirectResponse(url="/cadastros/motoristas/", status_code=303)


@router.post("/{motorista_id}/excluir")
def excluir_motorista(
    motorista_id: int,
    db: Session = Depends(get_db),
):
    motorista = motorista_service.buscar_motorista(db, motorista_id)

    if not motorista:
        raise HTTPException(status_code=404, detail="Motorista não encontrado.")

    motorista_service.excluir_motorista(db, motorista)

    return RedirectResponse(url="/cadastros/motoristas/", status_code=303)