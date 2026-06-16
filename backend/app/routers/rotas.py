from datetime import date
from decimal import Decimal, InvalidOperation

from fastapi import APIRouter, Depends, Form, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.municipio import Municipio
from app.schemas.rota import RotaCreate, RotaUpdate
from app.services import rota_service


router = APIRouter(prefix="/cadastros/rotas", tags=["Rotas"])


def buscar_municipio_por_id(db: Session, municipio_id: int | None):
    if not municipio_id:
        return None

    return (
        db.query(Municipio)
        .filter(Municipio.codigo_ibge == municipio_id)
        .first()
    )


def decimal_ou_none(valor: str | None):
    if not valor:
        return None

    try:
        return Decimal(valor.replace(",", "."))
    except InvalidOperation:
        return None


def date_ou_none(valor: str | None):
    if not valor:
        return None

    return date.fromisoformat(valor)


@router.get("/")
def listar_rotas(
    request: Request,
    origem: str | None = Query(None),
    destino: str | None = Query(None),
    status: str | None = Query(None),
    page: int = Query(1),
    db: Session = Depends(get_db),
):
    resultado = rota_service.listar_rotas(
        db=db,
        origem=origem,
        destino=destino,
        status=status,
        page=page,
        per_page=25,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/rotas.html",
        context={
            "rotas": resultado["items"],
            "total": resultado["total"],
            "page": resultado["page"],
            "per_page": resultado["per_page"],
            "total_pages": resultado["total_pages"],
            "filtro_origem": origem or "",
            "filtro_destino": destino or "",
            "filtro_status": status or "",
            "page_title": "Rotas - GrainDesk",
            "titulo_pagina": "Rotas",
            "subtitulo_pagina": "Cadastro de rotas município x município.",
        },
    )


@router.get("/nova")
def nova_rota(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/rota_form.html",
        context={
            "rota": None,
            "municipio_origem": None,
            "municipio_destino": None,
            "modo": "nova",
            "page_title": "Nova Rota - GrainDesk",
        },
    )


@router.post("/nova")
def criar_rota(
    municipio_origem_id: int = Form(...),
    municipio_destino_id: int = Form(...),
    distancia_km: str | None = Form(None),
    tarifa: str | None = Form(None),
    possui_pedagio: bool = Form(False),
    valor_pedagio_por_eixo: str | None = Form(None),
    observacao: str | None = Form(None),
    vigencia_inicio: str | None = Form(None),
    vigencia_fim: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    origem = buscar_municipio_por_id(db, municipio_origem_id)
    destino = buscar_municipio_por_id(db, municipio_destino_id)

    if not origem:
        raise HTTPException(status_code=400, detail="Município de origem inválido.")

    if not destino:
        raise HTTPException(status_code=400, detail="Município de destino inválido.")

    if municipio_origem_id == municipio_destino_id:
        raise HTTPException(status_code=400, detail="Origem e destino não podem ser iguais.")

    inicio = date_ou_none(vigencia_inicio)
    fim = date_ou_none(vigencia_fim)

    if inicio and fim and fim < inicio:
        raise HTTPException(status_code=400, detail="Vigência final não pode ser menor que a inicial.")

    if ativo and rota_service.existe_rota_ativa_duplicada(
        db=db,
        municipio_origem_id=municipio_origem_id,
        municipio_destino_id=municipio_destino_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="Já existe uma rota ativa cadastrada para esta origem e destino.",
        )

    dados = RotaCreate(
        municipio_origem_id=municipio_origem_id,
        municipio_destino_id=municipio_destino_id,
        distancia_km=decimal_ou_none(distancia_km),
        tarifa=decimal_ou_none(tarifa),
        possui_pedagio=possui_pedagio,
        valor_pedagio_por_eixo=decimal_ou_none(valor_pedagio_por_eixo) if possui_pedagio else None,
        observacao=observacao.strip() if observacao else None,
        vigencia_inicio=inicio,
        vigencia_fim=fim,
        ativo=ativo,
    )

    rota_service.criar_rota(db, dados)

    return RedirectResponse(url="/cadastros/rotas/", status_code=303)


@router.get("/{rota_id}/editar")
def editar_rota(rota_id: int, request: Request, db: Session = Depends(get_db)):
    rota = rota_service.buscar_rota(db, rota_id)

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada.")

    municipio_origem = buscar_municipio_por_id(db, rota.municipio_origem_id)
    municipio_destino = buscar_municipio_por_id(db, rota.municipio_destino_id)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/rota_form.html",
        context={
            "rota": rota,
            "municipio_origem": municipio_origem,
            "municipio_destino": municipio_destino,
            "modo": "editar",
            "page_title": "Editar Rota - GrainDesk",
        },
    )


@router.post("/{rota_id}/editar")
def atualizar_rota(
    rota_id: int,
    municipio_origem_id: int = Form(...),
    municipio_destino_id: int = Form(...),
    distancia_km: str | None = Form(None),
    tarifa: str | None = Form(None),
    possui_pedagio: bool = Form(False),
    valor_pedagio_por_eixo: str | None = Form(None),
    observacao: str | None = Form(None),
    vigencia_inicio: str | None = Form(None),
    vigencia_fim: str | None = Form(None),
    ativo: bool = Form(False),
    db: Session = Depends(get_db),
):
    rota = rota_service.buscar_rota(db, rota_id)

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada.")

    origem = buscar_municipio_por_id(db, municipio_origem_id)
    destino = buscar_municipio_por_id(db, municipio_destino_id)

    if not origem:
        raise HTTPException(status_code=400, detail="Município de origem inválido.")

    if not destino:
        raise HTTPException(status_code=400, detail="Município de destino inválido.")

    if municipio_origem_id == municipio_destino_id:
        raise HTTPException(status_code=400, detail="Origem e destino não podem ser iguais.")

    inicio = date_ou_none(vigencia_inicio)
    fim = date_ou_none(vigencia_fim)

    if inicio and fim and fim < inicio:
        raise HTTPException(status_code=400, detail="Vigência final não pode ser menor que a inicial.")

    if ativo and rota_service.existe_rota_ativa_duplicada(
        db=db,
        municipio_origem_id=municipio_origem_id,
        municipio_destino_id=municipio_destino_id,
        rota_id_ignorar=rota_id,
    ):
        raise HTTPException(
            status_code=400,
            detail="Já existe outra rota ativa cadastrada para esta origem e destino.",
        )

    dados = RotaUpdate(
        municipio_origem_id=municipio_origem_id,
        municipio_destino_id=municipio_destino_id,
        distancia_km=decimal_ou_none(distancia_km),
        tarifa=decimal_ou_none(tarifa),
        possui_pedagio=possui_pedagio,
        valor_pedagio_por_eixo=decimal_ou_none(valor_pedagio_por_eixo) if possui_pedagio else None,
        observacao=observacao.strip() if observacao else None,
        vigencia_inicio=inicio,
        vigencia_fim=fim,
        ativo=ativo,
    )

    rota_service.atualizar_rota(db, rota, dados)

    return RedirectResponse(url="/cadastros/rotas/", status_code=303)


@router.post("/{rota_id}/excluir")
def excluir_rota(rota_id: int, db: Session = Depends(get_db)):
    rota = rota_service.buscar_rota(db, rota_id)

    if not rota:
        raise HTTPException(status_code=404, detail="Rota não encontrada.")

    rota_service.excluir_rota(db, rota)

    return RedirectResponse(url="/cadastros/rotas/", status_code=303)