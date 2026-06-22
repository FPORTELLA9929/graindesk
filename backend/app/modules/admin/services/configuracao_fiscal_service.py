from sqlalchemy.orm import Session

from app.modules.cadastros.models.configuracao_fiscal import ConfiguracaoFiscal


def obter_configuracao_ativa(db: Session):
    configuracao = (
        db.query(ConfiguracaoFiscal)
        .filter(ConfiguracaoFiscal.ativo == True)
        .order_by(ConfiguracaoFiscal.id.desc())
        .first()
    )

    if configuracao:
        return configuracao

    configuracao = ConfiguracaoFiscal(
        ambiente="homologacao",
        uf_emitente="PR",
        versao_mdfe="3.00",
        versao_nfe="4.00",
        timeout_sefaz=30,
        tentativas_envio=3,
        contingencia_automatica=False,
        ativo=True,
    )

    db.add(configuracao)
    db.commit()
    db.refresh(configuracao)

    return configuracao


def salvar_configuracao(
    db: Session,
    ambiente: str,
    uf_emitente: str,
    versao_mdfe: str,
    versao_nfe: str,
    timeout_sefaz: int,
    tentativas_envio: int,
    contingencia_automatica: bool,
):
    configuracao = obter_configuracao_ativa(db)

    configuracao.ambiente = ambiente
    configuracao.uf_emitente = uf_emitente.upper()
    configuracao.versao_mdfe = versao_mdfe
    configuracao.versao_nfe = versao_nfe
    configuracao.timeout_sefaz = timeout_sefaz
    configuracao.tentativas_envio = tentativas_envio
    configuracao.contingencia_automatica = contingencia_automatica

    db.commit()
    db.refresh(configuracao)

    return configuracao