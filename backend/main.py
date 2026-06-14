from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.routers.empresas import router as empresas_router


BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(
    title="GrainDesk",
    description="GrainDesk - Plataforma Integrada de Gestão de Exportação",
    version="1.0.0"
)


templates = Jinja2Templates(
    directory=str(BASE_DIR / "frontend" / "templates")
)


app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "frontend" / "static")),
    name="static"
)


app.include_router(empresas_router)


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request,
        "dashboard/index.html",
        {
            "page_title": "Dashboard - GrainDesk"
        }
    )