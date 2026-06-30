from sqlalchemy.orm import Session

from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo
from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.models.exportacao_saida_item import ExportacaoSaidaItem
from app.modules.exportacao.services.exportacao_reprocessamento_service import (
    reprocessar_exportacoes,
)


def contar_registros_exportacao(db: Session) -> dict:
    return {
        "entradas": db.query(ExportacaoEntrada).count(),
        "saidas": db.query(ExportacaoSaida).count(),
        "itens_saida": db.query(ExportacaoSaidaItem).count(),
        "consumos": db.query(ExportacaoConsumo).count(),
    }


def limpar_tabela(db: Session, model) -> int:
    total = db.query(model).count()
    db.query(model).delete(synchronize_session=False)
    return total


def limpar_entradas_exportacao(db: Session) -> int:
    limpar_tabela(db, ExportacaoConsumo)

    total = limpar_tabela(db, ExportacaoEntrada)

    db.commit()

    return total


def limpar_saidas_exportacao(db: Session) -> int:
    limpar_tabela(db, ExportacaoConsumo)
    limpar_tabela(db, ExportacaoSaidaItem)

    total = limpar_tabela(db, ExportacaoSaida)

    db.commit()

    return total


def limpar_consumos_exportacao(db: Session) -> int:
    total = limpar_tabela(db, ExportacaoConsumo)

    db.commit()

    return total


def limpar_tudo_exportacao(db: Session) -> dict:
    total_consumos = limpar_tabela(db, ExportacaoConsumo)
    total_itens_saida = limpar_tabela(db, ExportacaoSaidaItem)
    total_saidas = limpar_tabela(db, ExportacaoSaida)
    total_entradas = limpar_tabela(db, ExportacaoEntrada)

    db.commit()

    return {
        "entradas": total_entradas,
        "saidas": total_saidas,
        "itens_saida": total_itens_saida,
        "consumos": total_consumos,
    }


def reprocessar_exportacoes_ferramenta(
    db: Session,
    usuario_id: int | None = None,
) -> dict:
    return reprocessar_exportacoes(
        db=db,
        usuario_id=usuario_id,
    )