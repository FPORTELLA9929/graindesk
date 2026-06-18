from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.schemas.usuario import UsuarioCreate
from app.modules.auth.services import auth_service
from utils.nomes import iniciais_nome, nome_abreviado


router = APIRouter(tags=["Autenticação"])


@router.get("/login")
async def login(request: Request):
    if request.session.get("usuario_logado"):
        return RedirectResponse(url="/dashboard", status_code=303)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="auth/login.html",
        context={
            "page_title": "Login - GrainDesk",
            "erro": None,
        },
    )


@router.post("/login")
async def login_post(
    request: Request,
    email: str = Form(...),
    senha: str = Form(...),
    db: Session = Depends(get_db),
):
    usuario = auth_service.autenticar_usuario(db, email, senha)

    if not usuario:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="auth/login.html",
            context={
                "page_title": "Login - GrainDesk",
                "erro": "E-mail ou senha inválidos, ou usuário ainda não aprovado.",
            },
            status_code=401,
        )

    permissoes = auth_service.listar_codigos_permissoes_usuario(db, usuario)

    request.session["usuario_logado"] = True
    request.session["usuario_id"] = usuario.id
    request.session["usuario_nome"] = usuario.nome
    request.session["usuario_nome_abreviado"] = nome_abreviado(usuario.nome)
    request.session["usuario_iniciais"] = iniciais_nome(usuario.nome)
    request.session["usuario_email"] = usuario.email
    request.session["usuario_perfil"] = usuario.perfil
    request.session["usuario_status"] = usuario.status
    request.session["permissoes"] = permissoes

    return RedirectResponse(url="/dashboard", status_code=303)


@router.get("/register")
async def register(request: Request):
    return request.app.state.templates.TemplateResponse(
        request=request,
        name="auth/register.html",
        context={
            "page_title": "Solicitar Acesso - GrainDesk",
            "erro": None,
        },
    )


@router.post("/register")
async def register_post(
    request: Request,
    nome: str = Form(...),
    empresa: str = Form(...),
    cnpj: str = Form(...),
    email: str = Form(...),
    telefone: str = Form(None),
    cargo: str = Form(None),
    senha: str = Form(...),
    confirmar_senha: str = Form(...),
    db: Session = Depends(get_db),
):
    try:
        dados = UsuarioCreate(
            nome=nome,
            empresa=empresa,
            cnpj=cnpj,
            email=email,
            telefone=telefone,
            cargo=cargo,
            senha=senha,
            confirmar_senha=confirmar_senha,
        )

        auth_service.criar_usuario(db, dados)

    except ValueError as erro:
        return request.app.state.templates.TemplateResponse(
            request=request,
            name="auth/register.html",
            context={
                "page_title": "Solicitar Acesso - GrainDesk",
                "erro": str(erro),
            },
            status_code=400,
        )

    return RedirectResponse(url="/login?cadastro=pendente", status_code=303)


@router.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/login", status_code=303)