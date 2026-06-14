from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.database.base import Base
from app.database.connection import engine
from app.models.empresa import Empresa
from app.routers.empresas import router as empresas_router


BASE_DIR = Path(__file__).resolve().parent.parent


app = FastAPI(
    title="GrainDesk",
    description="GrainDesk - Plataforma Integrada de Gestão de Exportação",
    version="1.0.0",
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


app.include_router(empresas_router)


@app.get("/")
async def dashboard(request: Request):
    return templates.TemplateResponse(
        request=request,
        name="dashboard/index.html",
        context={
            "page_title": "Dashboard - GrainDesk",
        },
    )


@app.get("/health")
async def health():
    return {
        "status": "ok",
        "sistema": "GrainDesk",
        "versao": "1.0.0",
    }