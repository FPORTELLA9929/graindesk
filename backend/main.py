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

from app.modules.auth.models.usuario import Usuario
from app.modules.cadastros.models.empresa import Empresa
from app.modules.cadastros.models.municipio import Municipio
from app.modules.cadastros.models.rota import Rota
from app.modules.cadastros.models.tipo_veiculo import TipoVeiculo
from app.modules.cadastros.models.transportador import Transportador
from app.modules.cadastros.models.transportador_dado_bancario import TransportadorDadoBancario
from app.modules.cadastros.models.veiculo import Veiculo, VeiculoPlaca
from app.modules.cadastros.models.cliente import Cliente
from app.modules.cadastros.models.fornecedor import Fornecedor
from app.modules.cadastros.models.motorista import Motorista

from app.modules.admin.models.certificado_digital import CertificadoDigital
from app.modules.admin.models.perfil import Perfil
from app.modules.admin.models.permissao import Permissao
from app.modules.admin.models.perfil_permissao import PerfilPermissao
from app.modules.admin.models.portal_unico_material import PortalUnicoMaterial
from app.modules.admin.models.portal_unico_urf import PortalUnicoURF
from app.modules.admin.models.portal_unico_recinto import PortalUnicoRecinto

from app.modules.portal_unico.models.portal_unico_token import PortalUnicoToken
from app.modules.portal_unico.models.portal_unico_consulta_cct import PortalUnicoConsultaCCT
from app.modules.portal_unico.models.portal_unico_consulta_cct_item import PortalUnicoConsultaCCTItem
from app.modules.portal_unico.models.portal_unico_cct_saldo import PortalUnicoCCTSaldo

from app.modules.cadastros.models.configuracao_fiscal import ConfiguracaoFiscal

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.models.mdfe_documento import MdfeDocumento

from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.models.exportacao_saida_item import ExportacaoSaidaItem
from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo
from app.modules.exportacao.models.exportacao_re import ExportacaoRE
from app.modules.exportacao.models.exportacao_processamento import ExportacaoProcessamento

from app.modules.auth.routers.auth import router as auth_router
from app.modules.cadastros.routers.empresas import router as empresas_router

from app.modules.admin.routers.admin_usuarios import router as admin_usuarios_router
from app.modules.admin.routers.admin_perfis import router as admin_perfis_router
from app.modules.admin.routers.admin_certificados import router as admin_certificados_router
from app.modules.admin.routers.admin_configuracoes_fiscais import (
    router as admin_configuracoes_fiscais_router,
)
from app.modules.admin.routers.admin_portal_unico import (
    router as admin_portal_unico_router,
)

from app.modules.cadastros.routers.rotas import router as rotas_router
from app.modules.cadastros.routers.municipios import router as municipios_router
from app.modules.cadastros.routers.tipos_veiculo import router as tipos_veiculo_router
from app.modules.cadastros.routers.transportadores import router as transportadores_router
from app.modules.cadastros.routers.veiculos import router as veiculos_router
from app.modules.cadastros.routers.clientes import router as clientes_router
from app.modules.cadastros.routers.fornecedores import router as fornecedores_router
from app.modules.cadastros.routers.motoristas import router as motoristas_router

from app.modules.mdfe.routers.mdfes import router as mdfes_router

from app.modules.exportacao.routers.exportacao_dashboard_router import (
    router as exportacao_dashboard_router,
)
from app.modules.exportacao.routers.exportacao_entrada_router import (
    router as exportacao_entrada_router,
)
from app.modules.exportacao.routers.exportacao_saida_router import (
    router as exportacao_saida_router,
)
from app.modules.exportacao.routers.consulta_averbacao_router import (
    router as consulta_averbacao_router,
)
from app.modules.portal_unico.routers.portal_unico_router import (
    router as portal_unico_router,
)

from app.modules.ferramentas.router import router as ferramentas_router

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
app.include_router(admin_certificados_router)
app.include_router(admin_configuracoes_fiscais_router)
app.include_router(admin_portal_unico_router)

app.include_router(rotas_router)
app.include_router(municipios_router)
app.include_router(tipos_veiculo_router)
app.include_router(transportadores_router)
app.include_router(veiculos_router)
app.include_router(clientes_router)
app.include_router(fornecedores_router)
app.include_router(motoristas_router)

app.include_router(mdfes_router)

app.include_router(exportacao_dashboard_router)
app.include_router(exportacao_entrada_router)
app.include_router(exportacao_saida_router)
app.include_router(consulta_averbacao_router)
app.include_router(portal_unico_router)

app.include_router(ferramentas_router)


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