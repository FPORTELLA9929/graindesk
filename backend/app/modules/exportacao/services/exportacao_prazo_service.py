from dataclasses import dataclass
from datetime import date, datetime


@dataclass
class PrazoExportacao:
    dias_restantes: int | None
    dias_decorridos: int | None
    situacao: str
    texto: str
    cor: str
    classe_badge: str


def _para_date(valor):
    if not valor:
        return None

    if isinstance(valor, datetime):
        return valor.date()

    if isinstance(valor, date):
        return valor

    return None


def calcular_prazo_exportacao(
    data_emissao,
    data_limite_exportacao,
    prazo_legal_dias: int = 180,
) -> PrazoExportacao:
    data_emissao_date = _para_date(data_emissao)
    data_limite_date = _para_date(data_limite_exportacao)

    if not data_emissao_date or not data_limite_date:
        return PrazoExportacao(
            dias_restantes=None,
            dias_decorridos=None,
            situacao="sem_data",
            texto="Sem data",
            cor="slate",
            classe_badge="bg-slate-100 text-slate-700",
        )

    hoje = date.today()

    dias_restantes = (data_limite_date - hoje).days
    dias_decorridos = prazo_legal_dias - dias_restantes

    if dias_restantes < 0:
        return PrazoExportacao(
            dias_restantes=dias_restantes,
            dias_decorridos=dias_decorridos,
            situacao="vencida",
            texto="Vencida",
            cor="black",
            classe_badge="bg-slate-900 text-white",
        )

    if dias_decorridos <= 120:
        return PrazoExportacao(
            dias_restantes=dias_restantes,
            dias_decorridos=dias_decorridos,
            situacao="normal",
            texto="Normal",
            cor="green",
            classe_badge="bg-emerald-100 text-emerald-700",
        )

    if dias_decorridos <= 150:
        return PrazoExportacao(
            dias_restantes=dias_restantes,
            dias_decorridos=dias_decorridos,
            situacao="atencao",
            texto="Atenção",
            cor="yellow",
            classe_badge="bg-yellow-100 text-yellow-700",
        )

    if dias_decorridos <= 170:
        return PrazoExportacao(
            dias_restantes=dias_restantes,
            dias_decorridos=dias_decorridos,
            situacao="critico",
            texto="Crítico",
            cor="orange",
            classe_badge="bg-orange-100 text-orange-700",
        )

    return PrazoExportacao(
        dias_restantes=dias_restantes,
        dias_decorridos=dias_decorridos,
        situacao="vencendo",
        texto="Vencendo",
        cor="red",
        classe_badge="bg-red-100 text-red-700",
    )