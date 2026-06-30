from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.admin.models.portal_unico_material import PortalUnicoMaterial
from app.modules.admin.models.portal_unico_urf import PortalUnicoURF
from app.modules.admin.models.portal_unico_recinto import PortalUnicoRecinto


router = APIRouter(
    prefix="/admin/portal-unico",
    tags=["Administração"],
)


ABAS = {
    "materiais": {
        "titulo": "Materiais / NCM",
        "model": PortalUnicoMaterial,
        "campo_codigo": "ncm",
        "label_codigo": "NCM",
        "placeholder_codigo": "Ex: 12019000",
        "placeholder_descricao": "Ex: SOJA EM GRÃOS",
    },
    "urfs": {
        "titulo": "URFs",
        "model": PortalUnicoURF,
        "campo_codigo": "codigo",
        "label_codigo": "Código",
        "placeholder_codigo": "Ex: 0817800",
        "placeholder_descricao": "Ex: PORTO DE SANTOS",
    },
    "recintos": {
        "titulo": "Recintos",
        "model": PortalUnicoRecinto,
        "campo_codigo": "codigo",
        "label_codigo": "Código",
        "placeholder_codigo": "Ex: 8931310",
        "placeholder_descricao": "Ex: Recinto Alfandegado",
    },
}


def usuario_admin_logado(request: Request):
    usuario = request.session.get("usuario_logado")

    if not usuario:
        return False

    perfil = request.session.get("usuario_perfil")

    return perfil == "administrador"


def obter_config_aba(aba: str):
    if aba not in ABAS:
        aba = "materiais"

    return aba, ABAS[aba]


@router.get("/")
async def portal_unico_admin(
    request: Request,
    aba: str = "materiais",
    busca: str | None = None,
    db: Session = Depends(get_db),
):
    if not usuario_admin_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    aba, config = obter_config_aba(aba)

    model = config["model"]
    campo_codigo = getattr(model, config["campo_codigo"])

    query = db.query(model)

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                campo_codigo.ilike(termo),
                model.descricao.ilike(termo),
            )
        )

    registros = (
        query
        .order_by(model.ativo.desc(), model.descricao.asc())
        .all()
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/portal_unico.html",
        context={
            "page_title": "Portal Único - GrainDesk",
            "titulo_pagina": "Portal Único",
            "subtitulo_pagina": "Manutenção administrativa de cadastros auxiliares do Portal Único",
            "aba": aba,
            "abas": ABAS,
            "config": config,
            "registros": registros,
            "busca": busca or "",
            "registro_edicao": None,
            "mensagem": None,
            "erro": None,
        },
    )


@router.post("/salvar")
async def salvar_portal_unico(
    request: Request,
    aba: str = Form(...),
    registro_id: int | None = Form(None),
    codigo: str = Form(...),
    descricao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not usuario_admin_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    aba, config = obter_config_aba(aba)

    model = config["model"]
    campo_nome = config["campo_codigo"]

    codigo = codigo.strip()
    descricao = descricao.strip()

    if not codigo or not descricao:
        return RedirectResponse(
            url=f"/admin/portal-unico/?aba={aba}",
            status_code=303,
        )

    if aba == "materiais":
        codigo = "".join(filter(str.isdigit, codigo))

        if len(codigo) != 8:
            return RedirectResponse(
                url=f"/admin/portal-unico/?aba={aba}",
                status_code=303,
            )

    if registro_id:
        registro = db.query(model).filter(model.id == registro_id).first()

        if registro:
            setattr(registro, campo_nome, codigo)
            registro.descricao = descricao
            registro.ativo = True
            db.commit()

    else:
        campo_codigo = getattr(model, campo_nome)

        existente = (
            db.query(model)
            .filter(campo_codigo == codigo)
            .first()
        )

        if existente:
            existente.descricao = descricao
            existente.ativo = True
        else:
            novo = model(
                **{
                    campo_nome: codigo,
                    "descricao": descricao,
                    "ativo": True,
                }
            )
            db.add(novo)

        db.commit()

    return RedirectResponse(
        url=f"/admin/portal-unico/?aba={aba}",
        status_code=303,
    )


@router.get("/editar/{registro_id}")
async def editar_portal_unico(
    registro_id: int,
    request: Request,
    aba: str = "materiais",
    busca: str | None = None,
    db: Session = Depends(get_db),
):
    if not usuario_admin_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    aba, config = obter_config_aba(aba)

    model = config["model"]

    registros = (
        db.query(model)
        .order_by(model.ativo.desc(), model.descricao.asc())
        .all()
    )

    registro_edicao = (
        db.query(model)
        .filter(model.id == registro_id)
        .first()
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/portal_unico.html",
        context={
            "page_title": "Portal Único - GrainDesk",
            "titulo_pagina": "Portal Único",
            "subtitulo_pagina": "Manutenção administrativa de cadastros auxiliares do Portal Único",
            "aba": aba,
            "abas": ABAS,
            "config": config,
            "registros": registros,
            "busca": busca or "",
            "registro_edicao": registro_edicao,
            "mensagem": None,
            "erro": None,
        },
    )


@router.post("/inativar/{registro_id}")
async def inativar_portal_unico(
    registro_id: int,
    request: Request,
    aba: str = Form(...),
    db: Session = Depends(get_db),
):
    if not usuario_admin_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    aba, config = obter_config_aba(aba)

    model = config["model"]

    registro = db.query(model).filter(model.id == registro_id).first()

    if registro:
        registro.ativo = False
        db.commit()

    return RedirectResponse(
        url=f"/admin/portal-unico/?aba={aba}",
        status_code=303,
    )


@router.post("/ativar/{registro_id}")
async def ativar_portal_unico(
    registro_id: int,
    request: Request,
    aba: str = Form(...),
    db: Session = Depends(get_db),
):
    if not usuario_admin_logado(request):
        return RedirectResponse(url="/login", status_code=303)

    aba, config = obter_config_aba(aba)

    model = config["model"]

    registro = db.query(model).filter(model.id == registro_id).first()

    if registro:
        registro.ativo = True
        db.commit()

    return RedirectResponse(
        url=f"/admin/portal-unico/?aba={aba}",
        status_code=303,
    )