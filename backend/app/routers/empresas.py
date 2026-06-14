from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.templating import Jinja2Templates


BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "frontend" / "templates")
)

router = APIRouter()


empresas_mock = [
    {
        "id": 1,
        "cnpj": "00.000.000/0001-00",
        "razao_social": "SIPAL INDUSTRIA E COMERCIO LTDA",
        "nome_fantasia": "SIPAL",
        "cidade": "Ibiporã",
        "uf": "PR",
        "tipo": "Exportador",
        "status": "Ativo",
        "responsavel": "Felipe Portella",
        "telefone": "(43) 99999-9999",
        "email": "contato@sipal.com.br",
    },
    {
        "id": 2,
        "cnpj": "11.111.111/0001-11",
        "razao_social": "TRADING ABC LTDA",
        "nome_fantasia": "Trading ABC",
        "cidade": "Londrina",
        "uf": "PR",
        "tipo": "Trading",
        "status": "Ativo",
        "responsavel": "Operacional ABC",
        "telefone": "(43) 98888-8888",
        "email": "operacional@tradingabc.com.br",
    },
    {
        "id": 3,
        "cnpj": "22.222.222/0001-22",
        "razao_social": "COOPERATIVA EXEMPLO",
        "nome_fantasia": "Cooperativa Exemplo",
        "cidade": "Maringá",
        "uf": "PR",
        "tipo": "Cooperativa",
        "status": "Inativo",
        "responsavel": "Departamento Exportação",
        "telefone": "(44) 97777-7777",
        "email": "exportacao@cooperativa.com.br",
    },
]


def buscar_empresa_por_id(empresa_id: int):
    for empresa in empresas_mock:
        if empresa["id"] == empresa_id:
            return empresa
    return None


@router.get("/empresas")
async def listar_empresas(request: Request):
    return templates.TemplateResponse(
        request,
        "cadastros/empresas.html",
        {
            "page_title": "Empresas - GrainDesk",
            "empresas": empresas_mock,
        },
    )


@router.get("/empresas/novo")
async def nova_empresa(request: Request):
    return templates.TemplateResponse(
        request,
        "cadastros/empresa_form.html",
        {
            "page_title": "Nova Empresa - GrainDesk",
            "modo": "novo",
            "empresa": None,
        },
    )


@router.get("/empresas/ver/{empresa_id}")
async def visualizar_empresa(request: Request, empresa_id: int):
    empresa = buscar_empresa_por_id(empresa_id)

    return templates.TemplateResponse(
        request,
        "cadastros/empresa_form.html",
        {
            "page_title": "Visualizar Empresa - GrainDesk",
            "modo": "visualizar",
            "empresa": empresa,
        },
    )


@router.get("/empresas/editar/{empresa_id}")
async def editar_empresa(request: Request, empresa_id: int):
    empresa = buscar_empresa_por_id(empresa_id)

    return templates.TemplateResponse(
        request,
        "cadastros/empresa_form.html",
        {
            "page_title": "Editar Empresa - GrainDesk",
            "modo": "editar",
            "empresa": empresa,
        },
    )