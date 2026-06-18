from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.core.permissoes import redirecionar_se_nao_logado_ou_sem_permissao
from app.database.session import get_db
from app.modules.admin.services import configuracao_fiscal_service


router = APIRouter(
    prefix="/admin/configuracoes-fiscais",
    tags=["Admin - Configurações Fiscais"],
)


@router.get("/")
async def configuracoes_fiscais(
    request: Request,
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="configuracoes_fiscais",
    )
    if redirect:
        return redirect

    configuracao = configuracao_fiscal_service.obter_configuracao_ativa(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="admin/configuracoes_fiscais.html",
        context={
            "page_title": "Configurações Fiscais - GrainDesk",
            "titulo_pagina": "Configurações Fiscais",
            "subtitulo_pagina": "Parâmetros fiscais para integrações SEFAZ.",
            "configuracao": configuracao,
            "erro": None,
        },
    )


@router.post("/")
async def salvar_configuracoes_fiscais(
    request: Request,
    ambiente: str = Form(...),
    uf_emitente: str = Form(...),
    versao_mdfe: str = Form(...),
    versao_nfe: str = Form(...),
    db: Session = Depends(get_db),
):
    redirect = redirecionar_se_nao_logado_ou_sem_permissao(
        db=db,
        request=request,
        codigo_permissao="configuracoes_fiscais",
    )
    if redirect:
        return redirect

    configuracao_fiscal_service.salvar_configuracao(
        db=db,
        ambiente=ambiente,
        uf_emitente=uf_emitente,
        versao_mdfe=versao_mdfe,
        versao_nfe=versao_nfe,
    )

    return RedirectResponse(
        url="/admin/configuracoes-fiscais/",
        status_code=303,
    )