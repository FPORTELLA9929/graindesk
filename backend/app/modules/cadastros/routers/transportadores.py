import re

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.models.municipio import Municipio
from app.modules.cadastros.schemas.transportador import (
    TransportadorCreate,
    TransportadorUpdate,
)
from app.modules.cadastros.schemas.transportador_dado_bancario import TransportadorDadoBancarioCreate
from app.modules.cadastros.services import transportador_service
from app.modules.cadastros.services import transportador_dado_bancario_service


router = APIRouter(prefix="/cadastros/transportadores", tags=["Transportadores"])


TIPOS_TRANSPORTADOR_VALIDOS = ["TAC", "ETC", "CTC"]
TIPOS_CONTA_VALIDOS = ["CORRENTE", "POUPANCA", "SALARIO", "PAGAMENTO", "OUTRA"]
TIPOS_PIX_VALIDOS = ["CPF", "CNPJ", "EMAIL", "TELEFONE", "ALEATORIA"]


def limpar_documento(valor: str | None) -> str | None:
    if not valor:
        return None
    return re.sub(r"\D", "", valor)


def texto_ou_none(valor: str | None) -> str | None:
    if not valor:
        return None

    valor = valor.strip()
    return valor or None


def municipio_existe(db: Session, municipio_id: int | None) -> bool:
    if not municipio_id:
        return False

    return (
        db.query(Municipio.codigo_ibge)
        .filter(Municipio.codigo_ibge == municipio_id)
        .first()
        is not None
    )


def buscar_municipio_por_id(db: Session, municipio_id: int | None):
    if not municipio_id:
        return None

    return (
        db.query(Municipio)
        .filter(Municipio.codigo_ibge == municipio_id)
        .first()
    )


def validar_tipo_transportador(tipo_transportador: str | None):
    if not tipo_transportador:
        return None

    tipo = tipo_transportador.strip().upper()

    if tipo not in TIPOS_TRANSPORTADOR_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de transportador inválido.")

    return tipo


def validar_tipo_conta(tipo_conta: str | None):
    if not tipo_conta:
        return None

    tipo = tipo_conta.strip().upper()
    return tipo if tipo in TIPOS_CONTA_VALIDOS else "OUTRA"


def validar_tipo_pix(tipo_pix: str | None):
    if not tipo_pix:
        return None

    tipo = tipo_pix.strip().upper()

    if tipo not in TIPOS_PIX_VALIDOS:
        raise HTTPException(status_code=400, detail="Tipo de PIX inválido.")

    return tipo


def existe_algum_dado_bancario(item: dict) -> bool:
    campos = [
        "banco_codigo",
        "banco_nome",
        "agencia",
        "conta",
        "digito_conta",
        "tipo_conta",
        "favorecido",
        "cpf_cnpj_favorecido",
        "tipo_pix",
        "chave_pix",
    ]

    return any(texto_ou_none(item.get(campo)) for campo in campos)


def montar_dados_bancarios(form, transportador_id: int):
    bancos_codigo = form.getlist("banco_codigo")
    bancos_nome = form.getlist("banco_nome")
    agencias = form.getlist("agencia")
    contas = form.getlist("conta")
    digitos_conta = form.getlist("digito_conta")
    tipos_conta = form.getlist("tipo_conta")
    favorecidos = form.getlist("favorecido")
    documentos_favorecidos = form.getlist("cpf_cnpj_favorecido")
    tipos_pix = form.getlist("tipo_pix")
    chaves_pix = form.getlist("chave_pix")
    principais = form.getlist("principal_bancario")
    ativos = form.getlist("ativo_bancario")

    total = max(
        len(bancos_codigo),
        len(bancos_nome),
        len(agencias),
        len(contas),
        len(digitos_conta),
        len(tipos_conta),
        len(favorecidos),
        len(documentos_favorecidos),
        len(tipos_pix),
        len(chaves_pix),
        len(principais),
        len(ativos),
        0,
    )

    dados = []
    principal_ja_definido = False

    for index in range(total):
        item = {
            "banco_codigo": bancos_codigo[index] if index < len(bancos_codigo) else None,
            "banco_nome": bancos_nome[index] if index < len(bancos_nome) else None,
            "agencia": agencias[index] if index < len(agencias) else None,
            "conta": contas[index] if index < len(contas) else None,
            "digito_conta": digitos_conta[index] if index < len(digitos_conta) else None,
            "tipo_conta": tipos_conta[index] if index < len(tipos_conta) else None,
            "favorecido": favorecidos[index] if index < len(favorecidos) else None,
            "cpf_cnpj_favorecido": (
                documentos_favorecidos[index]
                if index < len(documentos_favorecidos)
                else None
            ),
            "tipo_pix": tipos_pix[index] if index < len(tipos_pix) else None,
            "chave_pix": chaves_pix[index] if index < len(chaves_pix) else None,
            "principal": principais[index] if index < len(principais) else "false",
            "ativo": ativos[index] if index < len(ativos) else "true",
        }

        if not existe_algum_dado_bancario(item):
            continue

        principal = str(item["principal"]).lower() == "true"
        ativo = str(item["ativo"]).lower() == "true"

        if principal and principal_ja_definido:
            principal = False

        if principal:
            principal_ja_definido = True

        dados.append(
            TransportadorDadoBancarioCreate(
                transportador_id=transportador_id,
                banco_codigo=texto_ou_none(item["banco_codigo"]),
                banco_nome=texto_ou_none(item["banco_nome"]),
                agencia=texto_ou_none(item["agencia"]),
                conta=texto_ou_none(item["conta"]),
                digito_conta=texto_ou_none(item["digito_conta"]),
                tipo_conta=validar_tipo_conta(item["tipo_conta"]),
                favorecido=texto_ou_none(item["favorecido"]),
                cpf_cnpj_favorecido=limpar_documento(item["cpf_cnpj_favorecido"]),
                tipo_pix=validar_tipo_pix(item["tipo_pix"]),
                chave_pix=texto_ou_none(item["chave_pix"]),
                principal=principal,
                ativo=ativo,
            )
        )

    if dados and not any(item.principal for item in dados):
        dados[0].principal = True

    return dados


def salvar_dados_bancarios(db: Session, transportador_id: int, dados_bancarios):
    transportador_dado_bancario_service.excluir_por_transportador(
        db=db,
        transportador_id=transportador_id,
        commit=False,
    )

    transportador_dado_bancario_service.criar_varios_dados_bancarios(
        db=db,
        dados_bancarios=dados_bancarios,
        commit=False,
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
            "tem_proxima": resultado.get("tem_proxima", False),
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
            "dados_bancarios": [],
            "modo": "novo",
            "page_title": "Novo Transportador - GrainDesk",
            "titulo_pagina": "Novo Transportador",
            "subtitulo_pagina": "Inclua um novo transportador no cadastro.",
        },
    )


@router.post("/novo")
async def criar_transportador(request: Request, db: Session = Depends(get_db)):
    form = await request.form()

    tipo_pessoa = form.get("tipo_pessoa")
    nome_razao_social = form.get("nome_razao_social")
    cpf_cnpj = form.get("cpf_cnpj")
    municipio_id = form.get("municipio_id")

    if tipo_pessoa not in ["PF", "PJ"]:
        raise HTTPException(status_code=400, detail="Tipo de pessoa inválido.")

    if not texto_ou_none(nome_razao_social):
        raise HTTPException(status_code=400, detail="Nome/Razão Social é obrigatório.")

    if not texto_ou_none(cpf_cnpj):
        raise HTTPException(status_code=400, detail="CPF/CNPJ é obrigatório.")

    municipio_id_int = int(municipio_id) if municipio_id else None

    if not municipio_existe(db, municipio_id_int):
        raise HTTPException(status_code=400, detail="Município inválido.")

    cpf_cnpj_limpo = limpar_documento(cpf_cnpj)

    if transportador_service.buscar_por_cpf_cnpj(db, cpf_cnpj_limpo):
        raise HTTPException(
            status_code=400,
            detail="Já existe transportador cadastrado com este CPF/CNPJ.",
        )

    dados = TransportadorCreate(
        tipo_pessoa=tipo_pessoa,
        nome_razao_social=nome_razao_social.strip(),
        nome_fantasia=texto_ou_none(form.get("nome_fantasia")),
        cpf_cnpj=cpf_cnpj_limpo,
        rg_ie=texto_ou_none(form.get("rg_ie")),
        rntrc=texto_ou_none(form.get("rntrc")),
        tipo_transportador=validar_tipo_transportador(form.get("tipo_transportador")),
        antt_ativa=form.get("antt_ativa") == "true",
        telefone=texto_ou_none(form.get("telefone")),
        email=texto_ou_none(form.get("email")),
        municipio_id=municipio_id_int,
        endereco=texto_ou_none(form.get("endereco")),
        ativo=form.get("ativo") == "true",
    )

    try:
        transportador = transportador_service.criar_transportador(
            db=db,
            dados=dados,
            commit=False,
        )

        salvar_dados_bancarios(
            db=db,
            transportador_id=transportador.id,
            dados_bancarios=montar_dados_bancarios(form, transportador.id),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

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

    dados_bancarios = transportador_dado_bancario_service.listar_por_transportador(
        db=db,
        transportador_id=transportador_id,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="cadastros/transportador_form.html",
        context={
            "transportador": transportador,
            "municipio": municipio,
            "dados_bancarios": dados_bancarios,
            "modo": "editar",
            "page_title": "Editar Transportador - GrainDesk",
            "titulo_pagina": "Editar Transportador",
            "subtitulo_pagina": "Atualize os dados cadastrais do transportador.",
        },
    )


@router.post("/{transportador_id}/editar")
async def atualizar_transportador(
    transportador_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    transportador = transportador_service.buscar_transportador(db, transportador_id)

    if not transportador:
        raise HTTPException(status_code=404, detail="Transportador não encontrado.")

    form = await request.form()

    tipo_pessoa = form.get("tipo_pessoa")
    nome_razao_social = form.get("nome_razao_social")
    cpf_cnpj = form.get("cpf_cnpj")
    municipio_id = form.get("municipio_id")

    if tipo_pessoa not in ["PF", "PJ"]:
        raise HTTPException(status_code=400, detail="Tipo de pessoa inválido.")

    if not texto_ou_none(nome_razao_social):
        raise HTTPException(status_code=400, detail="Nome/Razão Social é obrigatório.")

    if not texto_ou_none(cpf_cnpj):
        raise HTTPException(status_code=400, detail="CPF/CNPJ é obrigatório.")

    municipio_id_int = int(municipio_id) if municipio_id else None

    if not municipio_existe(db, municipio_id_int):
        raise HTTPException(status_code=400, detail="Município inválido.")

    cpf_cnpj_limpo = limpar_documento(cpf_cnpj)

    existente = transportador_service.buscar_por_cpf_cnpj(db, cpf_cnpj_limpo)

    if existente and existente.id != transportador_id:
        raise HTTPException(
            status_code=400,
            detail="Já existe outro transportador cadastrado com este CPF/CNPJ.",
        )

    dados = TransportadorUpdate(
        tipo_pessoa=tipo_pessoa,
        nome_razao_social=nome_razao_social.strip(),
        nome_fantasia=texto_ou_none(form.get("nome_fantasia")),
        cpf_cnpj=cpf_cnpj_limpo,
        rg_ie=texto_ou_none(form.get("rg_ie")),
        rntrc=texto_ou_none(form.get("rntrc")),
        tipo_transportador=validar_tipo_transportador(form.get("tipo_transportador")),
        antt_ativa=form.get("antt_ativa") == "true",
        telefone=texto_ou_none(form.get("telefone")),
        email=texto_ou_none(form.get("email")),
        municipio_id=municipio_id_int,
        endereco=texto_ou_none(form.get("endereco")),
        ativo=form.get("ativo") == "true",
    )

    try:
        transportador_service.atualizar_transportador(
            db=db,
            transportador=transportador,
            dados=dados,
            commit=False,
        )

        salvar_dados_bancarios(
            db=db,
            transportador_id=transportador.id,
            dados_bancarios=montar_dados_bancarios(form, transportador.id),
        )

        db.commit()

    except Exception:
        db.rollback()
        raise

    return RedirectResponse(url="/cadastros/transportadores/", status_code=303)


@router.post("/{transportador_id}/excluir")
def excluir_transportador(transportador_id: int, db: Session = Depends(get_db)):
    transportador = transportador_service.buscar_transportador(db, transportador_id)

    if not transportador:
        raise HTTPException(status_code=404, detail="Transportador não encontrado.")

    transportador_service.excluir_transportador(db, transportador)

    return RedirectResponse(url="/cadastros/transportadores/", status_code=303)