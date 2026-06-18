from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, RedirectResponse
from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.core.permissoes import redirecionar_se_nao_logado_ou_sem_permissao
from app.database.session import get_db

from app.models.empresa import Empresa
from app.models.transportador import Transportador
from app.models.motorista import Motorista
from app.models.veiculo import Veiculo, VeiculoPlaca
from app.models.rota import Rota
from app.models.municipio import Municipio
from app.models.tipo_veiculo import TipoVeiculo

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.schemas.mdfe import MdfeCreate, MdfeUpdate
from app.modules.mdfe.services import mdfe_service
from app.modules.mdfe.services.mdfe_documento_service import importar_documento_xml_no_mdfe
from app.modules.mdfe.services.mdfe_xml_service import importar_xml_nfe


router = APIRouter(prefix="/mdfe", tags=["MDF-e"])


def moeda(valor: Decimal) -> Decimal:
    return valor.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def decimal_para_float(valor):
    if valor is None:
        return 0
    return float(valor)


def usuario_eh_administrador(request: Request) -> bool:
    perfil = request.session.get("usuario_perfil") or request.session.get("perfil")
    permissoes = request.session.get("permissoes", [])

    return perfil in ["administrador", "Administrador"] or (
        "perfis" in permissoes and "usuarios" in permissoes
    )


def obter_proximo_numero_mdfe(db: Session, empresa_id: int, serie: int = 1) -> int:
    ultimo_numero = (
        db.query(func.max(Mdfe.numero))
        .filter(Mdfe.empresa_id == empresa_id)
        .filter(Mdfe.serie == serie)
        .scalar()
    )

    return int(ultimo_numero) + 1 if ultimo_numero else 1


def montar_opcoes_veiculos(db: Session):
    placas = (
        db.query(VeiculoPlaca)
        .order_by(VeiculoPlaca.veiculo_id.asc(), VeiculoPlaca.id.asc())
        .all()
    )

    placa_por_veiculo = {}

    for placa in placas:
        if placa.veiculo_id not in placa_por_veiculo:
            placa_por_veiculo[placa.veiculo_id] = placa.placa

    veiculos = (
        db.query(Veiculo)
        .filter(Veiculo.ativo == True)
        .order_by(Veiculo.id.desc())
        .all()
    )

    return [
        {
            "id": veiculo.id,
            "descricao": placa_por_veiculo.get(veiculo.id) or f"Veículo #{veiculo.id}",
        }
        for veiculo in veiculos
    ]


def montar_opcoes_rotas(db: Session):
    Origem = aliased(Municipio)
    Destino = aliased(Municipio)

    resultados = (
        db.query(
            Rota,
            Origem.nome.label("origem_nome"),
            Destino.nome.label("destino_nome"),
        )
        .join(Origem, Rota.municipio_origem_id == Origem.codigo_ibge)
        .join(Destino, Rota.municipio_destino_id == Destino.codigo_ibge)
        .filter(Rota.ativo == True)
        .order_by(Rota.id.desc())
        .all()
    )

    opcoes = []

    for rota, origem_nome, destino_nome in resultados:
        opcoes.append(
            {
                "id": rota.id,
                "descricao": f"{origem_nome} x {destino_nome}",
                "tarifa": str(rota.tarifa or Decimal("0")),
                "pedagio_por_eixo": str(rota.valor_pedagio_por_eixo or Decimal("0")),
            }
        )

    return opcoes


def carregar_contexto_formulario(db: Session):
    return {
        "empresas": (
            db.query(Empresa)
            .filter(Empresa.ativo == True)
            .order_by(Empresa.razao_social.asc())
            .all()
        ),
        "transportadores": (
            db.query(Transportador)
            .order_by(Transportador.nome_razao_social.asc())
            .all()
        ),
        "motoristas": db.query(Motorista).order_by(Motorista.nome.asc()).all(),
        "veiculos": montar_opcoes_veiculos(db),
        "rotas": montar_opcoes_rotas(db),
    }


def calcular_memoria_frete(
    db: Session,
    rota_id: int,
    veiculo_id: int,
    peso_liquido: Decimal,
):
    rota = db.query(Rota).filter(Rota.id == rota_id).first()
    if not rota:
        raise ValueError("Rota não encontrada.")

    veiculo = db.query(Veiculo).filter(Veiculo.id == veiculo_id).first()
    if not veiculo:
        raise ValueError("Veículo não encontrado.")

    tipo_veiculo = (
        db.query(TipoVeiculo)
        .filter(TipoVeiculo.id == veiculo.tipo_veiculo_id)
        .first()
    )
    if not tipo_veiculo:
        raise ValueError("Tipo de veículo não encontrado.")

    tarifa_rota = rota.tarifa or Decimal("0")
    pedagio_por_eixo = rota.valor_pedagio_por_eixo or Decimal("0")
    quantidade_eixos = tipo_veiculo.quantidade_eixos or 0

    peso_toneladas = peso_liquido / Decimal("1000")
    frete_base = moeda(peso_toneladas * tarifa_rota)

    pedagio_total = (
        moeda(pedagio_por_eixo * Decimal(quantidade_eixos))
        if rota.possui_pedagio
        else Decimal("0.00")
    )

    frete_total = moeda(frete_base + pedagio_total)

    return {
        "tarifa_rota": tarifa_rota,
        "pedagio_por_eixo": pedagio_por_eixo,
        "frete_base": frete_base,
        "pedagio_total": pedagio_total,
        "frete_total": frete_total,
    }


@router.get("/")
async def listar_mdfes(request: Request, db: Session = Depends(get_db)):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    mdfes = mdfe_service.listar_mdfes(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="mdfe/mdfes.html",
        context={
            "page_title": "MDF-e - GrainDesk",
            "titulo_pagina": "MDF-e",
            "subtitulo_pagina": "Manifestos Eletrônicos cadastrados.",
            "mdfes": mdfes,
        },
    )


@router.post("/ler-xml")
async def ler_xml_mdfe(
    request: Request,
    rota_id: int = Form(...),
    veiculo_id: int = Form(...),
    arquivo_xml: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return JSONResponse(status_code=403, content={"erro": "Sem permissão."})

    try:
        dados_xml = importar_xml_nfe(arquivo_xml)
        peso_liquido = dados_xml.get("peso_liquido") or Decimal("0")

        memoria = calcular_memoria_frete(
            db=db,
            rota_id=rota_id,
            veiculo_id=veiculo_id,
            peso_liquido=peso_liquido,
        )

        return {
            "produto": dados_xml.get("produto") or "",
            "peso_liquido": decimal_para_float(peso_liquido),
            "tarifa_rota": decimal_para_float(memoria["tarifa_rota"]),
            "pedagio_por_eixo": decimal_para_float(memoria["pedagio_por_eixo"]),
            "frete_base": decimal_para_float(memoria["frete_base"]),
            "pedagio_total": decimal_para_float(memoria["pedagio_total"]),
            "frete_total": decimal_para_float(memoria["frete_total"]),
        }

    except ValueError as erro:
        return JSONResponse(status_code=400, content={"erro": str(erro)})


@router.get("/novo")
async def novo_mdfe(request: Request, db: Session = Depends(get_db)):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    admin = usuario_eh_administrador(request)
    contexto = carregar_contexto_formulario(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="mdfe/mdfe_form.html",
        context={
            "page_title": "Novo MDF-e - GrainDesk",
            "titulo_pagina": "Novo MDF-e",
            "subtitulo_pagina": "Cadastro inicial do Manifesto Eletrônico.",
            **contexto,
            "mdfe": None,
            "admin": admin,
            "modo_edicao": False,
            "numero_padrao": 1,
            "serie_padrao": 1,
            "erro": None,
        },
    )


@router.post("/novo")
async def criar_mdfe(
    request: Request,
    numero: int = Form(default=1),
    serie: int = Form(default=1),
    empresa_id: int = Form(...),
    transportador_id: int = Form(...),
    motorista_id: int = Form(...),
    veiculo_id: int = Form(...),
    rota_id: int = Form(...),
    uf_inicio: str = Form(...),
    uf_fim: str = Form(...),
    observacoes: str | None = Form(default=None),
    arquivo_xml: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    admin = usuario_eh_administrador(request)

    if not admin:
        serie = 1
        numero = obter_proximo_numero_mdfe(db=db, empresa_id=empresa_id, serie=serie)

    dados = MdfeCreate(
        numero=numero,
        serie=serie,
        empresa_id=empresa_id,
        transportador_id=transportador_id,
        motorista_id=motorista_id,
        veiculo_id=veiculo_id,
        rota_id=rota_id,
        uf_inicio=uf_inicio,
        uf_fim=uf_fim,
        observacoes=observacoes,
    )

    mdfe = mdfe_service.criar_mdfe(db=db, dados=dados)

    if arquivo_xml and arquivo_xml.filename:
        try:
            importar_documento_xml_no_mdfe(
                db=db,
                mdfe_id=mdfe.id,
                arquivo_xml=arquivo_xml,
            )
        except ValueError as erro:
            mdfe_service.excluir_mdfe(db, mdfe.id)
            contexto = carregar_contexto_formulario(db)

            return request.app.state.templates.TemplateResponse(
                request=request,
                name="mdfe/mdfe_form.html",
                context={
                    "page_title": "Novo MDF-e - GrainDesk",
                    "titulo_pagina": "Novo MDF-e",
                    "subtitulo_pagina": "Cadastro inicial do Manifesto Eletrônico.",
                    **contexto,
                    "mdfe": None,
                    "admin": admin,
                    "modo_edicao": False,
                    "numero_padrao": numero,
                    "serie_padrao": serie,
                    "erro": str(erro),
                },
            )

    return RedirectResponse(url="/mdfe/", status_code=303)


@router.get("/{mdfe_id}/editar")
async def editar_mdfe(
    mdfe_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    mdfe = mdfe_service.buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise HTTPException(status_code=404, detail="MDF-e não encontrado.")

    if mdfe.status != "rascunho":
        return RedirectResponse(url="/mdfe/", status_code=303)

    admin = usuario_eh_administrador(request)
    contexto = carregar_contexto_formulario(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="mdfe/mdfe_form.html",
        context={
            "page_title": "Editar MDF-e - GrainDesk",
            "titulo_pagina": "Editar MDF-e",
            "subtitulo_pagina": "Edição permitida apenas para MDF-e em rascunho.",
            **contexto,
            "mdfe": mdfe,
            "admin": admin,
            "modo_edicao": True,
            "numero_padrao": mdfe.numero,
            "serie_padrao": mdfe.serie,
            "erro": None,
        },
    )


@router.post("/{mdfe_id}/editar")
async def atualizar_mdfe(
    mdfe_id: int,
    request: Request,
    numero: int = Form(default=1),
    serie: int = Form(default=1),
    empresa_id: int = Form(...),
    transportador_id: int = Form(...),
    motorista_id: int = Form(...),
    veiculo_id: int = Form(...),
    rota_id: int = Form(...),
    uf_inicio: str = Form(...),
    uf_fim: str = Form(...),
    observacoes: str | None = Form(default=None),
    arquivo_xml: UploadFile | None = File(default=None),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    mdfe_atual = mdfe_service.buscar_mdfe(db, mdfe_id)

    if not mdfe_atual:
        raise HTTPException(status_code=404, detail="MDF-e não encontrado.")

    if mdfe_atual.status != "rascunho":
        return RedirectResponse(url="/mdfe/", status_code=303)

    admin = usuario_eh_administrador(request)

    if not admin:
        numero = mdfe_atual.numero
        serie = mdfe_atual.serie

    dados = MdfeUpdate(
        numero=numero,
        serie=serie,
        empresa_id=empresa_id,
        transportador_id=transportador_id,
        motorista_id=motorista_id,
        veiculo_id=veiculo_id,
        rota_id=rota_id,
        uf_inicio=uf_inicio,
        uf_fim=uf_fim,
        observacoes=observacoes,
    )

    mdfe_service.atualizar_mdfe(db, mdfe_id, dados)

    if arquivo_xml and arquivo_xml.filename:
        importar_documento_xml_no_mdfe(
            db=db,
            mdfe_id=mdfe_id,
            arquivo_xml=arquivo_xml,
        )

    return RedirectResponse(url="/mdfe/", status_code=303)


@router.post("/{mdfe_id}/excluir")
async def excluir_mdfe(
    mdfe_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db, request=request, codigo_permissao="mdfe"
    )
    if redirect:
        return redirect

    try:
        sucesso = mdfe_service.excluir_mdfe(db, mdfe_id)
    except ValueError:
        return RedirectResponse(url="/mdfe/", status_code=303)

    if not sucesso:
        raise HTTPException(status_code=404, detail="MDF-e não encontrado.")

    return RedirectResponse(url="/mdfe/", status_code=303)