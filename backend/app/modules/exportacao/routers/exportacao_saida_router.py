from datetime import datetime, time

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session, joinedload

from app.database.session import get_db
from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.services.exportacao_saida_service import (
    importar_xml_saida_exportacao,
)


router = APIRouter(
    prefix="/exportacao/saidas",
    tags=["Exportação"],
)


def listar_empresas_ativas(db: Session):
    return (
        db.query(Empresa)
        .filter(Empresa.ativo == True)
        .order_by(Empresa.razao_social.asc())
        .all()
    )


def _data_inicio(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.combine(
            datetime.strptime(valor, "%Y-%m-%d").date(),
            time.min,
        )
    except Exception:
        return None


def _data_fim(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.combine(
            datetime.strptime(valor, "%Y-%m-%d").date(),
            time.max,
        )
    except Exception:
        return None


def listar_saidas_com_historico(
    db: Session,
    empresa_id: int | None = None,
    destinatario: str | None = None,
    status: str | None = None,
    numero_nfe: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
):
    query = (
        db.query(ExportacaoSaida)
        .options(
            joinedload(ExportacaoSaida.empresa),
            joinedload(ExportacaoSaida.consumos),
        )
    )

    if empresa_id:
        query = query.filter(ExportacaoSaida.empresa_id == empresa_id)

    if destinatario:
        busca = f"%{destinatario.strip()}%"
        query = query.filter(ExportacaoSaida.destinatario_nome.ilike(busca))

    if status:
        query = query.filter(ExportacaoSaida.status == status)

    if numero_nfe:
        busca_nf = f"%{numero_nfe.strip()}%"
        query = query.filter(ExportacaoSaida.numero_nfe.ilike(busca_nf))

    data_ini = _data_inicio(data_inicial)
    if data_ini:
        query = query.filter(ExportacaoSaida.data_emissao >= data_ini)

    data_fim = _data_fim(data_final)
    if data_fim:
        query = query.filter(ExportacaoSaida.data_emissao <= data_fim)

    return query.order_by(ExportacaoSaida.criado_em.desc()).all()


def contexto_padrao(
    empresas,
    saidas,
    mensagem=None,
    erros=None,
    filtros=None,
):
    return {
        "page_title": "NF-e de Exportação - GrainDesk",
        "titulo_pagina": "NF-e de Exportação",
        "subtitulo_pagina": "Importação das NF-es de exportação e baixa automática do estoque",
        "empresas": empresas,
        "saidas": saidas,
        "mensagem": mensagem,
        "erros": erros or [],
        "filtros": filtros
        or {
            "empresa_id": None,
            "destinatario": "",
            "status": "",
            "numero_nfe": "",
            "data_inicial": "",
            "data_final": "",
        },
    }


@router.get("/")
async def tela_saidas(
    request: Request,
    empresa_id: int | None = None,
    destinatario: str | None = None,
    status: str | None = None,
    numero_nfe: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    db: Session = Depends(get_db),
):
    if not request.session.get("usuario_logado"):
        return RedirectResponse(url="/login", status_code=303)

    empresas = listar_empresas_ativas(db)

    saidas = listar_saidas_com_historico(
        db=db,
        empresa_id=empresa_id,
        destinatario=destinatario,
        status=status,
        numero_nfe=numero_nfe,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/saidas.html",
        context=contexto_padrao(
            empresas=empresas,
            saidas=saidas,
            filtros={
                "empresa_id": empresa_id,
                "destinatario": destinatario or "",
                "status": status or "",
                "numero_nfe": numero_nfe or "",
                "data_inicial": data_inicial or "",
                "data_final": data_final or "",
            },
        ),
    )


@router.post("/")
async def importar_saida(
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
            resultado = await importar_xml_saida_exportacao(
                db=db,
                empresa_id=empresa_id,
                arquivo_xml=arquivo_xml,
            )

            if resultado["status"] == "importada":
                importadas += 1
            elif resultado["status"] == "duplicada":
                duplicadas += 1
            else:
                erros.append(
                    f"{arquivo_xml.filename}: {resultado.get('mensagem', 'Não importada.')}"
                )

        except Exception as exc:
            db.rollback()
            erros.append(f"{arquivo_xml.filename}: {str(exc)}")

    saidas = listar_saidas_com_historico(db)

    mensagem = (
        f"Importação concluída. "
        f"Importadas: {importadas}. "
        f"Duplicadas: {duplicadas}."
    )

    return request.app.state.templates.TemplateResponse(
        request=request,
        name="exportacao/saidas.html",
        context=contexto_padrao(
            empresas=empresas,
            saidas=saidas,
            mensagem=mensagem,
            erros=erros,
        ),
    )