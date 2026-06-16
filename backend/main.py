import os
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database.base import Base
from app.database.connection import engine

from app.models.usuario import Usuario
from app.models.empresa import Empresa
from app.models.municipio import Municipio
from app.models.rota import Rota
from app.models.tipo_veiculo import TipoVeiculo
from app.models.transportador import Transportador
from app.models.veiculo import Veiculo, VeiculoPlaca
from app.models.cliente import Cliente
from app.models.fornecedor import Fornecedor
from app.models.motorista import Motorista

from app.models.perfil import Perfil
from app.models.permissao import Permissao
from app.models.perfil_permissao import PerfilPermissao

from app.routers.auth import router as auth_router
from app.routers.empresas import router as empresas_router
from app.routers.admin_usuarios import router as admin_usuarios_router
from app.routers.admin_perfis import router as admin_perfis_router
from app.routers.rotas import router as rotas_router
from app.routers.municipios import router as municipios_router
from app.routers.tipos_veiculo import router as tipos_veiculo_router
from app.routers.transportadores import router as transportadores_router
from app.routers.veiculos import router as veiculos_router
from app.routers.clientes import router as clientes_router
from app.routers.fornecedores import router as fornecedores_router
from app.routers.motoristas import router as motoristas_router


load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

app = FastAPI(
    title="GrainDesk",
    description="Plataforma Integrada de Gestão de Exportação",
    version="1.0.0",
)

SECRET_KEY = os.getenv("SECRET_KEY", "graindesk-dev-secret-key")

app.add_middleware(
    SessionMiddleware,
    secret_key=SECRET_KEY,
    max_age=60 * 60 * 8,
)

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(
    directory=str(BASE_DIR / "frontend" / "templates")
)

app.state.templates = templates

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "frontend" / "static")),
    name="static",
)

app.include_router(auth_router)
app.include_router(empresas_router)
app.include_router(admin_usuarios_router)
app.include_router(admin_perfis_router)
app.include_router(rotas_router)
app.include_router(municipios_router)
app.include_router(tipos_veiculo_router)
app.include_router(transportadores_router)
app.include_router(veiculos_router)
app.include_router(clientes_router)
app.include_router(fornecedores_router)
app.include_router(motoristas_router)


@app.get("/")
async def home():
    return RedirectResponse(url="/login", status_code=303)


@app.get("/dashboard")
async def dashboard(request: Request):

    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "page_title": "Dashboard - GrainDesk",
            "titulo_pagina": "Dashboard",
            "subtitulo_pagina": "Visão geral da operação",
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sistema": "GrainDesk",
        "versao": "1.0.0",
    }