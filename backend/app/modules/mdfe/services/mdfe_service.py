from sqlalchemy.orm import Session

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.models.mdfe_documento import MdfeDocumento
from app.modules.mdfe.schemas.mdfe import MdfeCreate, MdfeUpdate
from app.modules.mdfe.services.mdfe_chave_service import gerar_chave_mdfe
from app.modules.cadastros.models.municipio import Municipio


def listar_mdfes(db: Session):
    return (
        db.query(Mdfe)
        .order_by(Mdfe.id.desc())
        .all()
    )


def buscar_mdfe(db: Session, mdfe_id: int):
    return (
        db.query(Mdfe)
        .filter(Mdfe.id == mdfe_id)
        .first()
    )


def _buscar_municipio_origem(db: Session, mdfe: Mdfe):
    municipio = (
        db.query(Municipio)
        .filter(Municipio.codigo_ibge == mdfe.rota.municipio_origem_id)
        .first()
    )

    if not municipio:
        raise ValueError("Município de origem da rota não encontrado.")

    return municipio


def garantir_chave_mdfe(db: Session, mdfe_id: int) -> Mdfe:
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    if mdfe.chave_acesso and mdfe.codigo_mdf and mdfe.digito_verificador:
        return mdfe

    municipio_origem = _buscar_municipio_origem(db, mdfe)

    chave_mdfe = gerar_chave_mdfe(
        cuf=municipio_origem.codigo_uf,
        data_emissao=mdfe.criado_em,
        cnpj_emitente=mdfe.empresa.cnpj,
        serie=mdfe.serie,
        numero=mdfe.numero,
        tp_emis=1,
    )

    mdfe.chave_acesso = chave_mdfe["chave"]
    mdfe.codigo_mdf = chave_mdfe["cMDF"]
    mdfe.digito_verificador = chave_mdfe["cDV"]

    db.commit()
    db.refresh(mdfe)

    return mdfe


def criar_mdfe(db: Session, dados: MdfeCreate):
    mdfe = Mdfe(
        numero=dados.numero,
        serie=dados.serie,
        empresa_id=dados.empresa_id,
        transportador_id=dados.transportador_id,
        motorista_id=dados.motorista_id,
        veiculo_id=dados.veiculo_id,
        rota_id=dados.rota_id,
        uf_inicio=dados.uf_inicio,
        uf_fim=dados.uf_fim,
        status="rascunho",
        observacoes=dados.observacoes,
    )

    db.add(mdfe)
    db.commit()
    db.refresh(mdfe)

    garantir_chave_mdfe(db, mdfe.id)

    db.refresh(mdfe)

    return mdfe


def atualizar_mdfe(db: Session, mdfe_id: int, dados: MdfeUpdate):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        return None

    if mdfe.status != "rascunho":
        raise ValueError("Somente MDF-e em rascunho pode ser editado.")

    campos = dados.model_dump(exclude_unset=True)

    campos_que_mudam_chave = {
        "empresa_id",
        "rota_id",
        "serie",
        "numero",
    }

    deve_regerar_chave = any(
        campo in campos and getattr(mdfe, campo) != valor
        for campo, valor in campos.items()
        if campo in campos_que_mudam_chave
    )

    for campo, valor in campos.items():
        setattr(mdfe, campo, valor)

    if deve_regerar_chave:
        mdfe.chave_acesso = None
        mdfe.codigo_mdf = None
        mdfe.digito_verificador = None
        mdfe.xml_path = None
        mdfe.xml_assinado_path = None
        mdfe.mensagem_retorno = None

    db.commit()
    db.refresh(mdfe)

    garantir_chave_mdfe(db, mdfe.id)

    db.refresh(mdfe)

    return mdfe


def atualizar_xml_paths(
    db: Session,
    mdfe_id: int,
    xml_path: str | None = None,
    xml_assinado_path: str | None = None,
):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    if xml_path is not None:
        mdfe.xml_path = xml_path

    if xml_assinado_path is not None:
        mdfe.xml_assinado_path = xml_assinado_path

    db.commit()
    db.refresh(mdfe)

    return mdfe


def atualizar_retorno_sefaz(
    db: Session,
    mdfe_id: int,
    status: str,
    mensagem_retorno: str | None = None,
    protocolo: str | None = None,
    recibo: str | None = None,
):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    mdfe.status = status
    mdfe.mensagem_retorno = mensagem_retorno

    if protocolo is not None:
        mdfe.protocolo = protocolo

    if recibo is not None:
        mdfe.recibo = recibo

    db.commit()
    db.refresh(mdfe)

    return mdfe


def excluir_documentos_do_mdfe(db: Session, mdfe_id: int):
    (
        db.query(MdfeDocumento)
        .filter(MdfeDocumento.mdfe_id == mdfe_id)
        .delete(synchronize_session=False)
    )


def excluir_mdfe(db: Session, mdfe_id: int):
    mdfe = buscar_mdfe(db, mdfe_id)

    if not mdfe:
        return False

    if mdfe.status != "rascunho":
        raise ValueError("Somente MDF-e em rascunho pode ser excluído.")

    excluir_documentos_do_mdfe(db, mdfe_id)

    db.delete(mdfe)
    db.commit()

    return True