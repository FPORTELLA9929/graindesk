from urllib.parse import quote

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.ferramentas.service import (
    contar_registros_exportacao,
    limpar_consumos_exportacao,
    limpar_entradas_exportacao,
    limpar_saidas_exportacao,
    limpar_tudo_exportacao,
    reprocessar_exportacoes_ferramenta,
)


router = APIRouter(
    prefix="/ferramentas",
    tags=["Ferramentas"],
)


def usuario_eh_admin(request: Request) -> bool:
    if not request.session.get("usuario_logado"):
        return False

    return request.session.get("usuario_perfil") == "administrador"


def redirecionar_com_mensagem(mensagem: str):
    return RedirectResponse(
        url=f"/ferramentas/?mensagem={quote(mensagem)}",
        status_code=303,
    )


def redirecionar_com_erro(erro: str):
    return RedirectResponse(
        url=f"/ferramentas/?erro={quote(erro)}",
        status_code=303,
    )


@router.get("")
@router.get("/")
async def ferramentas_index(
    request: Request,
    mensagem: str | None = None,
    erro: str | None = None,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    contadores = contar_registros_exportacao(db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="ferramentas/index.html",
        context={
            "page_title": "Ferramentas - GrainDesk",
            "titulo_pagina": "Ferramentas",
            "subtitulo_pagina": "Ferramentas administrativas e de manutenção",
            "mensagem": mensagem,
            "erro": erro,
            "contadores": contadores,
        },
    )


@router.post("/limpar-entradas")
async def limpar_entradas(
    request: Request,
    confirmacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    if confirmacao != "APAGAR ENTRADAS":
        return redirecionar_com_erro("Confirmação inválida.")

    try:
        total = limpar_entradas_exportacao(db)
        return redirecionar_com_mensagem(
            f"{total} entrada(s) apagada(s) com sucesso."
        )

    except Exception as erro:
        db.rollback()
        return redirecionar_com_erro(f"Erro ao limpar entradas: {str(erro)}")


@router.post("/limpar-saidas")
async def limpar_saidas(
    request: Request,
    confirmacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    if confirmacao != "APAGAR SAIDAS":
        return redirecionar_com_erro("Confirmação inválida.")

    try:
        total = limpar_saidas_exportacao(db)
        return redirecionar_com_mensagem(
            f"{total} saída(s) apagada(s) com sucesso."
        )

    except Exception as erro:
        db.rollback()
        return redirecionar_com_erro(f"Erro ao limpar saídas: {str(erro)}")


@router.post("/limpar-consumos")
async def limpar_consumos(
    request: Request,
    confirmacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    if confirmacao != "APAGAR CONSUMOS":
        return redirecionar_com_erro("Confirmação inválida.")

    try:
        total = limpar_consumos_exportacao(db)
        return redirecionar_com_mensagem(
            f"{total} consumo(s) apagado(s) com sucesso."
        )

    except Exception as erro:
        db.rollback()
        return redirecionar_com_erro(f"Erro ao limpar consumos: {str(erro)}")


@router.post("/limpar-tudo")
async def limpar_tudo(
    request: Request,
    confirmacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    if confirmacao != "APAGAR TUDO":
        return redirecionar_com_erro("Confirmação inválida.")

    try:
        totais = limpar_tudo_exportacao(db)

        return redirecionar_com_mensagem(
            f"Limpeza concluída: {totais['entradas']} entrada(s), "
            f"{totais['saidas']} saída(s) e "
            f"{totais['consumos']} consumo(s) apagado(s)."
        )

    except Exception as erro:
        db.rollback()
        return redirecionar_com_erro(f"Erro ao limpar tudo: {str(erro)}")


@router.post("/reprocessar-exportacoes")
async def reprocessar_exportacoes(
    request: Request,
    confirmacao: str = Form(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    if not usuario_eh_admin(request):
        return RedirectResponse(url="/dashboard", status_code=303)

    if confirmacao != "REPROCESSAR EXPORTACOES":
        return redirecionar_com_erro("Confirmação inválida.")

    try:
        resultado = reprocessar_exportacoes_ferramenta(
            db=db,
            usuario_id=request.session.get("usuario_id"),
        )

        return redirecionar_com_mensagem(
            f"Reprocessamento concluído: "
            f"{resultado['entradas']} entrada(s), "
            f"{resultado['saidas']} saída(s), "
            f"{resultado['itens']} item(ns) e "
            f"{resultado['consumos']} consumo(s)."
        )

    except Exception as erro:
        db.rollback()

        return redirecionar_com_erro(
            f"Erro ao reprocessar exportações: {str(erro)}"
        )