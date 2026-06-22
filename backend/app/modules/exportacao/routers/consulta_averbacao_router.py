from fastapi import APIRouter, Request, Form
from fastapi.responses import RedirectResponse

router = APIRouter(
    prefix="/exportacao/averbacao",
    tags=["Exportação"],
)


@router.get("/")
async def tela_consulta_averbacao(request: Request):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_averbacao.html",
        context={
            "page_title": "Consulta Averbação - GrainDesk",
            "titulo_pagina": "Consulta Averbação",
            "subtitulo_pagina": "Consulta do evento 790700 - Averbação para Exportação",
            "chaves": "",
            "resultados": [],
        },
    )


@router.post("/")
async def consultar_averbacao(
    request: Request,
    chaves: str = Form(...),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    lista_chaves = [
        chave.strip()
        for chave in chaves.replace(",", "\n").splitlines()
        if chave.strip()
    ]

    resultados = []

    for chave in lista_chaves:
        resultados.append(
            {
                "chave": chave,
                "numero_due": "25BR0010150879",
                "item_nfe": "1",
                "item_due": "3",
                "quantidade_averbada": "23,89",
                "data_averbacao": "23/06/2025 09:10:12",
                "situacao": "Teste - Exportação Averbada",
            }
        )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/consulta_averbacao.html",
        context={
            "page_title": "Consulta Averbação - GrainDesk",
            "titulo_pagina": "Consulta Averbação",
            "subtitulo_pagina": "Consulta do evento 790700 - Averbação para Exportação",
            "chaves": chaves,
            "resultados": resultados,
        },
    )