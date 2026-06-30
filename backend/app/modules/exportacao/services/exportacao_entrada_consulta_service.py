from datetime import datetime, time
from decimal import Decimal
from math import ceil

from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.exportacao.models.exportacao_entrada import (
    ExportacaoEntrada,
    ExportacaoEntradaReserva,
    ExportacaoEntradaReservaItem,
)
from app.modules.exportacao.services.exportacao_prazo_service import (
    calcular_prazo_exportacao,
)


PAGINAS_PERMITIDAS = [10, 50, 100, 500]


def _int_ou_none(valor):
    if valor in (None, ""):
        return None

    try:
        return int(valor)
    except Exception:
        return None


def _decimal(valor) -> Decimal:
    if valor is None:
        return Decimal("0")

    try:
        return Decimal(str(valor))
    except Exception:
        return Decimal("0")


def _data_inicio(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.combine(datetime.strptime(valor, "%Y-%m-%d").date(), time.min)
    except Exception:
        return None


def _data_fim(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.combine(datetime.strptime(valor, "%Y-%m-%d").date(), time.max)
    except Exception:
        return None


def normalizar_empresa_id(empresa_id):
    return _int_ou_none(empresa_id)


def normalizar_paginacao(pagina: int | None, por_pagina: int | None):
    pagina = max(pagina or 1, 1)

    if por_pagina not in PAGINAS_PERMITIDAS:
        por_pagina = 10

    return pagina, por_pagina


def anexar_prazo_exportacao(entradas):
    for entrada in entradas:
        entrada.prazo_exportacao = calcular_prazo_exportacao(
            data_emissao=entrada.data_emissao,
            data_limite_exportacao=entrada.data_limite_exportacao,
            prazo_legal_dias=entrada.prazo_legal_dias or 180,
        )

    return entradas


def montar_query_entradas(
    db: Session,
    empresa_id: int | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
):
    query = db.query(ExportacaoEntrada)

    if empresa_id:
        query = query.filter(ExportacaoEntrada.empresa_id == empresa_id)

    if fornecedor:
        query = query.filter(
            ExportacaoEntrada.fornecedor_nome.ilike(f"%{fornecedor.strip()}%")
        )

    if status:
        query = query.filter(ExportacaoEntrada.status == status)

    if situacao_prazo:
        query = query.filter(ExportacaoEntrada.situacao_prazo == situacao_prazo)

    data_ini = _data_inicio(data_inicial)
    if data_ini:
        query = query.filter(ExportacaoEntrada.data_emissao >= data_ini)

    data_fim = _data_fim(data_final)
    if data_fim:
        query = query.filter(ExportacaoEntrada.data_emissao <= data_fim)

    return query


def _ids_entradas_filtradas(
    db: Session,
    empresa_id: int | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
):
    query = montar_query_entradas(
        db=db,
        empresa_id=empresa_id,
        fornecedor=fornecedor,
        status=status,
        situacao_prazo=situacao_prazo,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    return query.with_entities(ExportacaoEntrada.id).subquery()


def calcular_total_reservado_consulta(
    db: Session,
    empresa_id: int | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
) -> Decimal:
    entradas_filtradas = _ids_entradas_filtradas(
        db=db,
        empresa_id=empresa_id,
        fornecedor=fornecedor,
        status=status,
        situacao_prazo=situacao_prazo,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    total = (
        db.query(
            func.coalesce(
                func.sum(
                    ExportacaoEntradaReservaItem.quantidade_reservada
                    - ExportacaoEntradaReservaItem.quantidade_consumida
                ),
                0,
            )
        )
        .join(
            ExportacaoEntradaReserva,
            ExportacaoEntradaReserva.id == ExportacaoEntradaReservaItem.reserva_id,
        )
        .filter(ExportacaoEntradaReservaItem.entrada_id.in_(entradas_filtradas))
        .filter(ExportacaoEntradaReservaItem.status == "ativa")
        .filter(ExportacaoEntradaReserva.status.in_(["ativa", "parcial"]))
        .scalar()
    )

    reservado = _decimal(total)

    if reservado < 0:
        return Decimal("0")

    return reservado


def calcular_totais_consulta(
    db: Session,
    empresa_id: int | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
):
    query = montar_query_entradas(
        db=db,
        empresa_id=empresa_id,
        fornecedor=fornecedor,
        status=status,
        situacao_prazo=situacao_prazo,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    totais = query.with_entities(
        func.coalesce(func.sum(ExportacaoEntrada.quantidade_original), 0),
        func.coalesce(func.sum(ExportacaoEntrada.quantidade_saldo), 0),
    ).first()

    original = _decimal(totais[0] if totais else 0)
    saldo = _decimal(totais[1] if totais else 0)
    consumido = original - saldo

    reservado = calcular_total_reservado_consulta(
        db=db,
        empresa_id=empresa_id,
        fornecedor=fornecedor,
        status=status,
        situacao_prazo=situacao_prazo,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    livre = saldo - reservado

    if livre < 0:
        livre = Decimal("0")

    return {
        "original": original,
        "consumido": consumido,
        "saldo": saldo,
        "reservado": reservado,
        "livre": livre,
    }


def listar_entradas_com_historico(
    db: Session,
    empresa_id: int | None = None,
    fornecedor: str | None = None,
    status: str | None = None,
    situacao_prazo: str | None = None,
    data_inicial: str | None = None,
    data_final: str | None = None,
    pagina: int = 1,
    por_pagina: int = 10,
):
    pagina, por_pagina = normalizar_paginacao(
        pagina=pagina,
        por_pagina=por_pagina,
    )

    query_base = montar_query_entradas(
        db=db,
        empresa_id=empresa_id,
        fornecedor=fornecedor,
        status=status,
        situacao_prazo=situacao_prazo,
        data_inicial=data_inicial,
        data_final=data_final,
    )

    total_registros = query_base.count()
    total_paginas = max(ceil(total_registros / por_pagina), 1)

    if pagina > total_paginas:
        pagina = total_paginas

    entradas = (
        query_base.options(
            joinedload(ExportacaoEntrada.empresa),
            joinedload(ExportacaoEntrada.consumos),
            joinedload(ExportacaoEntrada.reservas_itens).joinedload(
                ExportacaoEntradaReservaItem.reserva
            ),
        )
        .order_by(ExportacaoEntrada.criado_em.desc())
        .limit(por_pagina)
        .offset((pagina - 1) * por_pagina)
        .all()
    )

    return {
        "entradas": anexar_prazo_exportacao(entradas),
        "paginacao": {
            "pagina": pagina,
            "por_pagina": por_pagina,
            "total_registros": total_registros,
            "total_paginas": total_paginas,
            "tem_anterior": pagina > 1,
            "tem_proxima": pagina < total_paginas,
            "pagina_anterior": max(pagina - 1, 1),
            "proxima_pagina": min(pagina + 1, total_paginas),
        },
        "totais_consulta": calcular_totais_consulta(
            db=db,
            empresa_id=empresa_id,
            fornecedor=fornecedor,
            status=status,
            situacao_prazo=situacao_prazo,
            data_inicial=data_inicial,
            data_final=data_final,
        ),
    }