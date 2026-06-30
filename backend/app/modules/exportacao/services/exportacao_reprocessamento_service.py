from sqlalchemy.orm import Session
from sqlalchemy.sql import func

from app.modules.exportacao.models.exportacao_consumo import ExportacaoConsumo
from app.modules.exportacao.models.exportacao_entrada import ExportacaoEntrada
from app.modules.exportacao.models.exportacao_processamento import (
    ExportacaoProcessamento,
)
from app.modules.exportacao.models.exportacao_saida import ExportacaoSaida
from app.modules.exportacao.models.exportacao_saida_item import ExportacaoSaidaItem
from app.modules.exportacao.services.exportacao_rastreabilidade_service import (
    processar_saida_exportacao,
)


def reprocessar_exportacoes(
    db: Session,
    usuario_id: int | None = None,
) -> dict:
    processamento = ExportacaoProcessamento(
        tipo="reprocessamento_exportacoes",
        status="executando",
        usuario_id=usuario_id,
    )

    db.add(processamento)
    db.flush()

    try:
        total_entradas = db.query(ExportacaoEntrada).count()
        total_saidas = db.query(ExportacaoSaida).count()
        total_itens = db.query(ExportacaoSaidaItem).count()

        db.query(ExportacaoConsumo).delete(synchronize_session=False)

        entradas = db.query(ExportacaoEntrada).all()

        for entrada in entradas:
            entrada.quantidade_saldo = entrada.quantidade_original
            entrada.status = "disponivel"
            db.add(entrada)

        db.flush()

        saidas = (
            db.query(ExportacaoSaida)
            .order_by(
                ExportacaoSaida.data_emissao.asc(),
                ExportacaoSaida.id.asc(),
            )
            .all()
        )

        total_consumos = 0

        for saida in saidas:
            consumos = processar_saida_exportacao(
                db=db,
                saida=saida,
            )

            total_consumos += len(consumos)

        processamento.status = "concluido"
        processamento.entradas_processadas = total_entradas
        processamento.saidas_processadas = total_saidas
        processamento.itens_processados = total_itens
        processamento.consumos_gerados = total_consumos
        processamento.mensagem = "Reprocessamento de exportações concluído com sucesso."
        processamento.finalizado_em = func.now()

        db.add(processamento)
        db.commit()

        return {
            "status": "concluido",
            "entradas": total_entradas,
            "saidas": total_saidas,
            "itens": total_itens,
            "consumos": total_consumos,
            "mensagem": processamento.mensagem,
        }

    except Exception as erro:
        db.rollback()

        processamento = ExportacaoProcessamento(
            tipo="reprocessamento_exportacoes",
            status="erro",
            usuario_id=usuario_id,
            erro=str(erro),
            mensagem="Erro ao reprocessar exportações.",
            finalizado_em=func.now(),
        )

        db.add(processamento)
        db.commit()

        raise