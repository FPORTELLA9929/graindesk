from datetime import datetime, timedelta
from decimal import Decimal
from io import BytesIO

from fastapi import UploadFile
from openpyxl import Workbook
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from app.modules.cadastros.models.empresa import Empresa
from app.modules.exportacao.models.exportacao_entrada import (
    ExportacaoEntrada,
    ExportacaoEntradaReserva,
    ExportacaoEntradaReservaItem,
)
from app.modules.exportacao.services.exportacao_entrada_xml_service import (
    ler_xml_entrada_equiparada,
)


CFOPS_ENTRADA_PROPRIA = {
    "1501",
    "2501",
}

PRAZO_LEGAL_EXPORTACAO_DIAS = 180


def _data_xml_para_datetime(valor: str | None):
    if not valor:
        return None

    try:
        return datetime.fromisoformat(valor.replace("Z", "+00:00"))
    except Exception:
        return None


def _somente_digitos(valor: str | None) -> str:
    if not valor:
        return ""

    return "".join(filter(str.isdigit, str(valor)))


def _cfop_limpo(valor: str | None) -> str:
    return _somente_digitos(valor)


def _decimal(valor) -> Decimal:
    if valor is None or valor == "":
        return Decimal("0")

    try:
        return Decimal(str(valor))
    except Exception:
        return Decimal("0")


def _cnpj_empresa_xml(dados: dict) -> tuple[str | None, str | None, str]:
    cfop = _cfop_limpo(dados.get("cfop"))

    if cfop in CFOPS_ENTRADA_PROPRIA:
        return (
            dados.get("emitente_cnpj"),
            dados.get("emitente_nome"),
            "emitente",
        )

    return (
        dados.get("destinatario_cnpj"),
        dados.get("destinatario_nome"),
        "destinatário",
    )


def calcular_data_limite_exportacao(
    data_emissao: datetime | None,
    prazo_dias: int = PRAZO_LEGAL_EXPORTACAO_DIAS,
):
    if not data_emissao:
        return None

    return data_emissao + timedelta(days=prazo_dias)


def calcular_situacao_prazo(
    data_limite_exportacao: datetime | None,
) -> str:
    if not data_limite_exportacao:
        return "sem_data"

    hoje = datetime.now(data_limite_exportacao.tzinfo).date()
    data_limite = data_limite_exportacao.date()

    dias_restantes = (data_limite - hoje).days
    dias_decorridos = PRAZO_LEGAL_EXPORTACAO_DIAS - dias_restantes

    if dias_restantes < 0:
        return "vencida"

    if dias_decorridos <= 120:
        return "normal"

    if dias_decorridos <= 150:
        return "atencao"

    if dias_decorridos <= 170:
        return "critico"

    return "vencendo"


def obter_empresa_por_cnpj(
    db: Session,
    cnpj: str | None,
    origem: str,
):
    cnpj_limpo = _somente_digitos(cnpj)

    if not cnpj_limpo:
        raise ValueError(f"XML não possui CNPJ do {origem}.")

    empresa = (
        db.query(Empresa)
        .filter(Empresa.cnpj == cnpj_limpo)
        .first()
    )

    if not empresa:
        raise ValueError(
            f"Empresa não encontrada no cadastro para o CNPJ do {origem} do XML: "
            f"{cnpj_limpo}."
        )

    if not empresa.ativo:
        raise ValueError(
            f"Empresa encontrada pelo CNPJ do {origem}, porém está inativa: "
            f"{empresa.razao_social} - {cnpj_limpo}."
        )

    return empresa


async def importar_xml_entrada_equiparada(
    db: Session,
    empresa_id: int | None,
    arquivo_xml: UploadFile,
):
    conteudo = await arquivo_xml.read()

    dados = ler_xml_entrada_equiparada(conteudo)

    cnpj_empresa, nome_empresa_xml, origem_cnpj = _cnpj_empresa_xml(dados)

    empresa = obter_empresa_por_cnpj(
        db=db,
        cnpj=cnpj_empresa,
        origem=origem_cnpj,
    )

    if empresa_id and empresa.id != empresa_id:
        raise ValueError(
            "A empresa selecionada não corresponde à empresa identificada no XML. "
            f"Empresa selecionada ID: {empresa_id}. "
            f"Empresa identificada pelo {origem_cnpj}: "
            f"{nome_empresa_xml or '-'} ({cnpj_empresa or '-'})."
        )

    existente = (
        db.query(ExportacaoEntrada)
        .filter(ExportacaoEntrada.chave_nfe == dados["chave_nfe"])
        .first()
    )

    if existente:
        return {
            "status": "duplicada",
            "mensagem": "NF-e de entrada já importada.",
            "entrada": existente,
        }

    data_emissao = _data_xml_para_datetime(dados["data_emissao"])
    data_limite_exportacao = calcular_data_limite_exportacao(data_emissao)
    situacao_prazo = calcular_situacao_prazo(data_limite_exportacao)

    entrada = ExportacaoEntrada(
        empresa_id=empresa.id,
        chave_nfe=dados["chave_nfe"],
        numero_nfe=dados["numero_nfe"],
        serie=dados["serie"],
        fornecedor_nome=dados["fornecedor_nome"],
        fornecedor_cnpj=dados["fornecedor_cnpj"],
        data_emissao=data_emissao,
        prazo_legal_dias=PRAZO_LEGAL_EXPORTACAO_DIAS,
        data_limite_exportacao=data_limite_exportacao,
        situacao_prazo=situacao_prazo,
        cfop=dados["cfop"],
        ncm=dados["ncm"],
        produto=dados["produto"],
        quantidade_original=Decimal(dados["quantidade_original"]),
        quantidade_saldo=Decimal(dados["quantidade_saldo"]),
        valor_original=Decimal(dados["valor_original"]),
        status="disponivel",
    )

    db.add(entrada)
    db.commit()
    db.refresh(entrada)

    return {
        "status": "importada",
        "mensagem": "NF-e de entrada importada com sucesso.",
        "entrada": entrada,
    }


def calcular_quantidade_reservada_ativa(
    db: Session,
    entrada_id: int,
) -> Decimal:
    reservado = (
        db.query(func.coalesce(func.sum(ExportacaoEntradaReservaItem.quantidade_reservada), 0))
        .join(
            ExportacaoEntradaReserva,
            ExportacaoEntradaReserva.id == ExportacaoEntradaReservaItem.reserva_id,
        )
        .filter(ExportacaoEntradaReservaItem.entrada_id == entrada_id)
        .filter(ExportacaoEntradaReservaItem.status == "ativa")
        .filter(ExportacaoEntradaReserva.status.in_(["ativa", "parcial"]))
        .scalar()
    )

    return _decimal(reservado)


def calcular_saldo_livre_para_reserva(
    db: Session,
    entrada: ExportacaoEntrada,
) -> Decimal:
    saldo = _decimal(entrada.quantidade_saldo)
    reservado = calcular_quantidade_reservada_ativa(db, entrada.id)

    saldo_livre = saldo - reservado

    if saldo_livre < 0:
        return Decimal("0")

    return saldo_livre


def listar_produtos_disponiveis_para_reserva(
    db: Session,
    empresa_id: int | None = None,
):
    query = (
        db.query(
            ExportacaoEntrada.ncm,
            ExportacaoEntrada.produto,
        )
        .filter(ExportacaoEntrada.quantidade_saldo > 0)
        .filter(ExportacaoEntrada.status.in_(["disponivel", "parcial"]))
    )

    if empresa_id:
        query = query.filter(ExportacaoEntrada.empresa_id == empresa_id)

    return (
        query
        .group_by(ExportacaoEntrada.ncm, ExportacaoEntrada.produto)
        .order_by(ExportacaoEntrada.produto.asc())
        .all()
    )


def criar_reserva_saldo_entrada(
    db: Session,
    empresa_id: int,
    quantidade_solicitada,
    ncm: str | None = None,
    produto: str | None = None,
    observacoes: str | None = None,
    criado_por: str | None = None,
):
    quantidade_solicitada = _decimal(quantidade_solicitada)

    if quantidade_solicitada <= 0:
        raise ValueError("Informe uma quantidade maior que zero para reservar.")

    empresa = (
        db.query(Empresa)
        .filter(Empresa.id == empresa_id)
        .first()
    )

    if not empresa:
        raise ValueError("Filial não encontrada.")

    query = (
        db.query(ExportacaoEntrada)
        .options(joinedload(ExportacaoEntrada.empresa))
        .filter(ExportacaoEntrada.empresa_id == empresa_id)
        .filter(ExportacaoEntrada.quantidade_saldo > 0)
        .filter(ExportacaoEntrada.status.in_(["disponivel", "parcial"]))
    )

    if ncm:
        query = query.filter(ExportacaoEntrada.ncm == ncm)

    if produto:
        query = query.filter(ExportacaoEntrada.produto == produto)

    entradas = (
        query
        .order_by(
            ExportacaoEntrada.data_limite_exportacao.asc().nullslast(),
            ExportacaoEntrada.data_emissao.asc().nullslast(),
            ExportacaoEntrada.id.asc(),
        )
        .all()
    )

    if not entradas:
        raise ValueError("Não há saldo disponível para reserva nessa filial/produto.")

    reserva = ExportacaoEntradaReserva(
        empresa_id=empresa_id,
        produto=produto,
        ncm=ncm,
        quantidade_solicitada=quantidade_solicitada,
        quantidade_reservada=Decimal("0"),
        quantidade_consumida=Decimal("0"),
        status="ativa",
        observacoes=observacoes,
        criado_por=criado_por,
    )

    db.add(reserva)
    db.flush()

    restante = quantidade_solicitada
    total_reservado = Decimal("0")

    for entrada in entradas:
        if restante <= 0:
            break

        saldo_livre = calcular_saldo_livre_para_reserva(db, entrada)

        if saldo_livre <= 0:
            continue

        quantidade_reservar = saldo_livre if saldo_livre <= restante else restante

        item = ExportacaoEntradaReservaItem(
            reserva_id=reserva.id,
            entrada_id=entrada.id,
            chave_nfe=entrada.chave_nfe,
            numero_nfe=entrada.numero_nfe,
            quantidade_reservada=quantidade_reservar,
            quantidade_consumida=Decimal("0"),
            status="ativa",
        )

        db.add(item)

        total_reservado += quantidade_reservar
        restante -= quantidade_reservar

    if total_reservado <= 0:
        db.rollback()
        raise ValueError("Não foi possível reservar saldo para os filtros informados.")

    reserva.quantidade_reservada = total_reservado

    if total_reservado < quantidade_solicitada:
        reserva.status = "parcial"

    db.commit()
    db.refresh(reserva)

    return reserva


def obter_reserva_com_itens(
    db: Session,
    reserva_id: int,
):
    reserva = (
        db.query(ExportacaoEntradaReserva)
        .options(
            joinedload(ExportacaoEntradaReserva.empresa),
            joinedload(ExportacaoEntradaReserva.itens)
            .joinedload(ExportacaoEntradaReservaItem.entrada)
            .joinedload(ExportacaoEntrada.empresa),
        )
        .filter(ExportacaoEntradaReserva.id == reserva_id)
        .first()
    )

    if not reserva:
        raise ValueError("Reserva não encontrada.")

    return reserva


def gerar_excel_reserva_saldo(
    db: Session,
    reserva_id: int,
) -> BytesIO:
    reserva = obter_reserva_com_itens(db, reserva_id)

    wb = Workbook()
    ws = wb.active
    ws.title = "Reserva de Saldo"

    cabecalho = [
        "Reserva",
        "Status Reserva",
        "Filial",
        "Produto",
        "NCM",
        "NF Entrada",
        "Chave de Acesso",
        "Data Emissão",
        "Vencimento 180 dias",
        "Dias Restantes",
        "Quantidade Reservada",
    ]

    ws.append(cabecalho)

    hoje = datetime.now().date()

    itens_ordenados = sorted(
        reserva.itens,
        key=lambda item: (
            item.entrada.data_limite_exportacao or datetime.max,
            item.entrada.data_emissao or datetime.max,
            item.id,
        ),
    )

    for item in itens_ordenados:
        entrada = item.entrada

        data_emissao = entrada.data_emissao.strftime("%d/%m/%Y") if entrada.data_emissao else ""
        vencimento = (
            entrada.data_limite_exportacao.strftime("%d/%m/%Y")
            if entrada.data_limite_exportacao
            else ""
        )

        dias_restantes = ""
        if entrada.data_limite_exportacao:
            dias_restantes = (entrada.data_limite_exportacao.date() - hoje).days

        ws.append(
            [
                reserva.id,
                reserva.status,
                reserva.empresa.razao_social if reserva.empresa else "",
                entrada.produto or reserva.produto or "",
                entrada.ncm or reserva.ncm or "",
                entrada.numero_nfe or "",
                entrada.chave_nfe,
                data_emissao,
                vencimento,
                dias_restantes,
                float(item.quantidade_reservada or 0),
            ]
        )

    for coluna in ws.columns:
        maior = 0
        letra = coluna[0].column_letter

        for celula in coluna:
            valor = str(celula.value or "")
            if len(valor) > maior:
                maior = len(valor)

        ws.column_dimensions[letra].width = min(maior + 2, 60)

    arquivo = BytesIO()
    wb.save(arquivo)
    arquivo.seek(0)

    return arquivo