import re

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.tipo_veiculo import TipoVeiculo
from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate

import app.services.veiculo_service as veiculo_service
import app.services.transportador_service as transportador_service
import app.services.tipo_veiculo_service as tipo_veiculo_service


router = APIRouter(
    prefix="/cadastros/veiculos",
    tags=["Veículos"],
)


def limpar_placa(valor: str | None) -> str | None:
    if not valor:
        return None
    return re.sub(r"[^A-Z0-9]", "", valor.upper().strip())


def limpar_documento(valor: str | None) -> str | None:
    if not valor:
        return None
    return re.sub(r"\D", "", valor)


def placa_valida(placa: str | None) -> bool:
    placa = limpar_placa(placa)

    if not placa:
        return False

    placa_antiga = re.fullmatch(r"[A-Z]{3}[0-9]{4}", placa)
    placa_mercosul = re.fullmatch(r"[A-Z]{3}[0-9][A-Z][0-9]{2}", placa)

    return bool(placa_antiga or placa_mercosul)


def documento_valido(documento: str | None) -> bool:
    if not documento:
        return True

    documento_limpo = limpar_documento(documento)

    return len(documento_limpo) in [11, 14]


def descricoes_esperadas(qtd: int) -> list[str]:
    if qtd == 1:
        return ["Placa Cavalo"]

    if qtd == 2:
        return ["Placa Cavalo", "Placa Carreta 1"]

    if qtd == 3:
        return ["Placa Cavalo", "Placa Carreta 1", "Placa Carreta 2"]

    if qtd == 4:
        return ["Placa Cavalo", "Placa Carreta 1", "Placa Dolly", "Placa Carreta 2"]

    return []


def carregar_selects(db: Session):
    transportadores_resultado = transportador_service.listar_transportadores(db)
    tipos_resultado = tipo_veiculo_service.listar_tipos_veiculo(db)

    return {
        "transportadores": [item[0] for item in transportadores_resultado["items"]],
        "tipos_veiculo": tipos_resultado["items"],
    }


def montar_dados_placas(form, quantidade_placas: int):
    descricoes = form.getlist("descricao_placa")
    placas = form.getlist("placa")
    documentos = form.getlist("cpf_cnpj_proprietario")
    rntrcs = form.getlist("rntrc")

    if len(placas) != quantidade_placas:
        raise HTTPException(
            status_code=400,
            detail=f"O tipo de veículo selecionado exige {quantidade_placas} placa(s).",
        )

    descricoes_corretas = descricoes_esperadas(quantidade_placas)
    dados_placas = []

    for index in range(quantidade_placas):
        descricao = descricoes[index] if index < len(descricoes) else ""
        placa = placas[index] if index < len(placas) else ""
        documento = documentos[index] if index < len(documentos) else None
        rntrc = rntrcs[index] if index < len(rntrcs) else None

        placa_limpa = limpar_placa(placa)
        documento_limpo = limpar_documento(documento)

        if descricao not in descricoes_corretas:
            raise HTTPException(status_code=400, detail="Descrição de placa inválida.")

        if not placa_valida(placa_limpa):
            raise HTTPException(
                status_code=400,
                detail="Placa inválida. Use o formato AAA-5969 ou AAA-5F98.",
            )

        if not documento_valido(documento_limpo):
            raise HTTPException(
                status_code=400,
                detail="CPF/CNPJ do proprietário inválido.",
            )

        dados_placas.append(
            {
                "descricao": descricao,
                "placa": placa_limpa,
                "cpf_cnpj_proprietario": documento_limpo,
                "rntrc": rntrc.strip() if rntrc else None,
            }
        )

    return dados_placas


@router.get("/")
def listar_veiculos(
    request: Request,
    busca: str | None = None,
    tipo_veiculo_id: int | None = None,
    status: str | None = None,
    db: Session = Depends(get_db),
):
    veiculos = veiculo_service.listar_veiculos(
        db=db,
        busca=busca,
        tipo_veiculo_id=tipo_veiculo_id,
        status=status,
    )

    selects = carregar_selects(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/veiculos.html",
        context={
            "veiculos": veiculos,
            "tipos_veiculo": selects["tipos_veiculo"],
            "filtros": {
                "busca": busca or "",
                "tipo_veiculo_id": tipo_veiculo_id or "",
                "status": status or "",
            },
            "page_title": "Veículos - GrainDesk",
            "titulo_pagina": "Veículos",
            "subtitulo_pagina": "Cadastro de conjuntos de veículos.",
        },
    )


@router.get("/novo")
def novo_veiculo(
    request: Request,
    db: Session = Depends(get_db),
):
    selects = carregar_selects(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/veiculo_form.html",
        context={
            "modo": "novo",
            "veiculo": None,
            "placas": [],
            "transportadores": selects["transportadores"],
            "tipos_veiculo": selects["tipos_veiculo"],
            "page_title": "Novo Veículo - GrainDesk",
            "titulo_pagina": "Novo Veículo",
            "subtitulo_pagina": "Cadastro de conjuntos veiculares.",
        },
    )


@router.post("/novo")
async def salvar_veiculo(
    request: Request,
    db: Session = Depends(get_db),
):
    form = await request.form()

    transportador_id = form.get("transportador_id")
    tipo_veiculo_id = form.get("tipo_veiculo_id")
    observacao = form.get("observacao") or None

    if not transportador_id:
        raise HTTPException(status_code=400, detail="Transportador é obrigatório.")

    if not tipo_veiculo_id:
        raise HTTPException(status_code=400, detail="Tipo de veículo é obrigatório.")

    tipo_veiculo = db.query(TipoVeiculo).filter(TipoVeiculo.id == int(tipo_veiculo_id)).first()

    if not tipo_veiculo:
        raise HTTPException(status_code=400, detail="Tipo de veículo inválido.")

    quantidade_placas = int(tipo_veiculo.quantidade_placas or 0)
    dados_placas = montar_dados_placas(form, quantidade_placas)

    dados_veiculo = VeiculoCreate(
        transportador_id=int(transportador_id),
        tipo_veiculo_id=int(tipo_veiculo_id),
        observacao=observacao.strip() if observacao else None,
        ativo=True,
    )

    veiculo = veiculo_service.criar_veiculo(db, dados_veiculo)

    for item in dados_placas:
        veiculo_service.criar_placa(
            db=db,
            veiculo_id=veiculo.id,
            descricao=item["descricao"],
            placa=item["placa"],
            cpf_cnpj_proprietario=item["cpf_cnpj_proprietario"],
            rntrc=item["rntrc"],
        )

    return RedirectResponse(url="/cadastros/veiculos/", status_code=303)


@router.get("/{veiculo_id}/editar")
def editar_veiculo(
    veiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    veiculo = veiculo_service.buscar_veiculo(db, veiculo_id)

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    placas = veiculo_service.buscar_placas_veiculo(db, veiculo_id)
    selects = carregar_selects(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/veiculo_form.html",
        context={
            "modo": "editar",
            "veiculo": veiculo,
            "placas": placas,
            "transportadores": selects["transportadores"],
            "tipos_veiculo": selects["tipos_veiculo"],
            "page_title": "Editar Veículo - GrainDesk",
            "titulo_pagina": "Editar Veículo",
            "subtitulo_pagina": "Atualização de conjunto veicular.",
        },
    )


@router.post("/{veiculo_id}/editar")
async def atualizar_veiculo(
    veiculo_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    veiculo = veiculo_service.buscar_veiculo(db, veiculo_id)

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    form = await request.form()

    transportador_id = form.get("transportador_id")
    tipo_veiculo_id = form.get("tipo_veiculo_id")
    observacao = form.get("observacao") or None
    ativo = form.get("ativo") == "on"

    if not transportador_id:
        raise HTTPException(status_code=400, detail="Transportador é obrigatório.")

    if not tipo_veiculo_id:
        raise HTTPException(status_code=400, detail="Tipo de veículo é obrigatório.")

    tipo_veiculo = db.query(TipoVeiculo).filter(TipoVeiculo.id == int(tipo_veiculo_id)).first()

    if not tipo_veiculo:
        raise HTTPException(status_code=400, detail="Tipo de veículo inválido.")

    quantidade_placas = int(tipo_veiculo.quantidade_placas or 0)
    dados_placas = montar_dados_placas(form, quantidade_placas)

    dados_veiculo = VeiculoUpdate(
        transportador_id=int(transportador_id),
        tipo_veiculo_id=int(tipo_veiculo_id),
        observacao=observacao.strip() if observacao else None,
        ativo=ativo,
    )

    veiculo_service.atualizar_veiculo(db, veiculo, dados_veiculo)

    veiculo_service.excluir_placas_veiculo(db, veiculo.id)

    for item in dados_placas:
        veiculo_service.criar_placa(
            db=db,
            veiculo_id=veiculo.id,
            descricao=item["descricao"],
            placa=item["placa"],
            cpf_cnpj_proprietario=item["cpf_cnpj_proprietario"],
            rntrc=item["rntrc"],
        )

    return RedirectResponse(url="/cadastros/veiculos/", status_code=303)


@router.post("/{veiculo_id}/excluir")
def excluir_veiculo(
    veiculo_id: int,
    db: Session = Depends(get_db),
):
    veiculo = veiculo_service.buscar_veiculo(db, veiculo_id)

    if not veiculo:
        raise HTTPException(status_code=404, detail="Veículo não encontrado.")

    veiculo_service.excluir_veiculo(db, veiculo)

    return RedirectResponse(url="/cadastros/veiculos/", status_code=303)