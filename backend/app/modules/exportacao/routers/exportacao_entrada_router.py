from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse, StreamingResponse
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.services.exportacao_entrada_consulta_service import (
    listar_entradas_com_historico,
    normalizar_empresa_id,
)
from app.modules.exportacao.services.exportacao_entrada_service import (
    criar_reserva_saldo_entrada,
    gerar_excel_reserva_saldo,
    importar_xml_entrada_equiparada,
    listar_produtos_disponiveis_para_reserva,
)

router = APIRouter(prefix="/exportacao/entradas", tags=["Exportação"])


def listar_empresas_ativas(db: Session):
    return (
        db.query(Empresa)
        .filter(Empresa.ativo == True)
        .order_by(Empresa.razao_social.asc())
        .all()
    )


def _usuario_criador_reserva(request: Request) -> str:
    usuario_logado = request.session.get("usuario_logado")
    usuario = request.session.get("usuario")

    for valor in (usuario, usuario_logado):
        if isinstance(valor, dict):
            return (
                valor.get("nome")
                or valor.get("nome_abreviado")
                or valor.get("email")
                or valor.get("usuario")
                or "Sistema"
            )

    return "Sistema"


def contexto_padrao(
    empresas,
    entradas,
    mensagem=None,
    erros=None,
    filtros=None,
    produtos_reserva=None,
    paginacao=None,
    totais_consulta=None,
):
    return {
        "page_title": "Entradas Equiparadas - GrainDesk",
        "titulo_pagina": "Entradas Equiparadas",
        "subtitulo_pagina": "Importação de NF-e de compra para formação do saldo de exportação",
        "empresas": empresas,
        "entradas": entradas,
        "mensagem": mensagem,
        "erros": erros or [],
        "produtos_reserva": produtos_reserva or [],
        "totais_consulta": totais_consulta
        or {
            "original": 0,
            "consumido": 0,
            "saldo": 0,
            "reservado": 0,
            "livre": 0,
        },
        "paginacao": paginacao
        or {
            "pagina": 1,
            "por_pagina": 10,
            "total_registros": len(entradas or []),
            "total_paginas": 1,
            "tem_anterior": False,
            "tem_proxima": False,
            "pagina_anterior": 1,
            "proxima_pagina": 1,
        },
        "filtros": filtros
        or {
            "empresa_id": None,
            "fornecedor": "",
            "status": "",
            "situacao_prazo": "",
            "data_inicial": "",
            "data_final": "",
            "pagina": 1,
            "por_pagina": 10,
        },
    }


@router.get("/")
async def tela_entradas(
    request: Request,
    empresa_id: str | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    pagina: int = 1,
    por_pagina: int = 10,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    empresa_id_int = normalizar_empresa_id(empresa_id)

    empresas = listar_empresas_ativas(db)

    resultado = listar_entradas_com_historico(
        db=db,
        empresa_id=empresa_id_int,
        fornecedor=fornecedor or None,
        status=status or None,
        situacao_prazo=situacao_prazo or None,
        data_inicial=data_inicial or None,
        data_final=data_final or None,
        pagina=pagina,
        por_pagina=por_pagina,
    )

    produtos_reserva = listar_produtos_disponiveis_para_reserva(
        db=db,
        empresa_id=empresa_id_int,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/entradas.html",
        context=contexto_padrao(
            empresas=empresas,
            entradas=resultado["entradas"],
            produtos_reserva=produtos_reserva,
            paginacao=resultado["paginacao"],
            totais_consulta=resultado["totais_consulta"],
            filtros={
                "empresa_id": empresa_id_int,
                "fornecedor": fornecedor or "",
                "status": status or "",
                "situacao_prazo": situacao_prazo or "",
                "data_inicial": data_inicial or "",
                "data_final": data_final or "",
                "pagina": resultado["paginacao"]["pagina"],
                "por_pagina": resultado["paginacao"]["por_pagina"],
            },
        ),
    )


@router.post("/")
async def importar_xml(
    request: Request,
    empresa_id: int | None = Form(None),
    arquivos_xml: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    empresas = listar_empresas_ativas(db)

    importadas = 0
    duplicadas = 0
    erros = []

    for arquivo_xml in arquivos_xml:
        try:
            resultado_importacao = await importar_xml_entrada_equiparada(
                db=db,
                empresa_id=empresa_id,
                arquivo_xml=arquivo_xml,
            )

            if resultado_importacao["status"] == "importada":
                importadas += 1
            elif resultado_importacao["status"] == "duplicada":
                duplicadas += 1

        except Exception as exc:
            db.rollback()
            erros.append(f"{arquivo_xml.filename}: {str(exc)}")

    resultado = listar_entradas_com_historico(
        db=db,
        pagina=1,
        por_pagina=10,
    )

    produtos_reserva = listar_produtos_disponiveis_para_reserva(db=db)

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/entradas.html",
        context=contexto_padrao(
            empresas=empresas,
            entradas=resultado["entradas"],
            produtos_reserva=produtos_reserva,
            paginacao=resultado["paginacao"],
            totais_consulta=resultado["totais_consulta"],
            mensagem=(
                f"Importação concluída. "
                f"Importadas: {importadas}. "
                f"Duplicadas: {duplicadas}."
            ),
            erros=erros,
        ),
    )


@router.post("/reservas")
async def reservar_saldo(
    request: Request,
    empresa_id: int = Form(...),
    quantidade_solicitada: str = Form(...),
    ncm: str | None = Form(None),
    produto: str | None = Form(None),
    observacoes: str | None = Form(None),
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    criado_por = _usuario_criador_reserva(request)

    try:
        reserva = criar_reserva_saldo_entrada(
            db=db,
            empresa_id=empresa_id,
            quantidade_solicitada=quantidade_solicitada,
            ncm=ncm or None,
            produto=produto or None,
            observacoes=observacoes,
            criado_por=criado_por,
        )

        return RedirectResponse(
            url=f"/exportacao/entradas/reservas/{reserva.id}/excel",
            status_code=303,
        )

    except Exception as exc:
        db.rollback()

        empresas = listar_empresas_ativas(db)

        resultado = listar_entradas_com_historico(
            db=db,
            pagina=1,
            por_pagina=10,
        )

        produtos_reserva = listar_produtos_disponiveis_para_reserva(db=db)

        return request.app.state.templates.TemplateResponse(
            request=request,
            name="exportacao/entradas.html",
            context=contexto_padrao(
                empresas=empresas,
                entradas=resultado["entradas"],
                produtos_reserva=produtos_reserva,
                paginacao=resultado["paginacao"],
                totais_consulta=resultado["totais_consulta"],
                erros=[str(exc)],
            ),
        )


@router.get("/reservas/{reserva_id}/excel")
async def baixar_excel_reserva(
    request: Request,
    reserva_id: int,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    arquivo = gerar_excel_reserva_saldo(
        db=db,
        reserva_id=reserva_id,
    )

    return StreamingResponse(
        arquivo,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="reserva_saldo_{reserva_id}.xlsx"'
        },
    )
