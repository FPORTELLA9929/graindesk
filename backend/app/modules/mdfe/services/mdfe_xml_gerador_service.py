from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy.orm import Session

from app.modules.cadastros.models.municipio import Municipio
from app.modules.cadastros.models.veiculo import VeiculoPlaca
from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.models.mdfe_documento import MdfeDocumento
from app.modules.mdfe.services.mdfe_chave_service import gerar_chave_mdfe


PASTA_XML_GERADOS = Path("app/modules/mdfe/xml/gerados")
FUSO_BRASIL = timezone(timedelta(hours=-3))
VERSAO_MDFE = "3.00"
VERSAO_MODAL = "3.00"
VER_PROC = "GrainDesk 1.0"

CODIGO_UF_PARA_SIGLA = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


# -----------------------------------------------------------------------------
# Helpers básicos
# -----------------------------------------------------------------------------

def _somente_numeros(valor) -> str:
    return "" if not valor else "".join(filter(str.isdigit, str(valor)))


def _limpar_rntrc(valor) -> str:
    return _somente_numeros(valor).lstrip("0")


def _texto(valor, padrao: str = "") -> str:
    return padrao if valor is None else str(valor).strip()


def _inteiro(valor, padrao: str = "0") -> str:
    if valor in (None, ""):
        return padrao
    try:
        return str(int(valor))
    except Exception:
        return padrao


def _decimal(valor, casas: int = 2) -> str:
    return f"{Decimal(valor or 0):.{casas}f}"


def _get(objeto, *campos, padrao=""):
    if objeto is None:
        return padrao

    for campo in campos:
        if hasattr(objeto, campo):
            valor = getattr(objeto, campo)
            if valor is not None:
                return valor

    return padrao


def _add(pai: Element, tag: str, texto=None, padrao: str = "") -> Element:
    elemento = SubElement(pai, tag)
    elemento.text = _texto(texto, padrao)
    return elemento


def _pretty_xml(elemento: Element) -> str:
    bruto = tostring(elemento, encoding="utf-8")
    return minidom.parseString(bruto).toprettyxml(
        indent="    ",
        encoding="utf-8",
    ).decode("utf-8")


# -----------------------------------------------------------------------------
# Datas, UF, municípios e consultas auxiliares
# -----------------------------------------------------------------------------

def _data_emissao_mdfe(mdfe: Mdfe) -> datetime:
    data = (mdfe.criado_em or datetime.now(FUSO_BRASIL)).replace(microsecond=0)

    if data.tzinfo is None:
        data = data.replace(tzinfo=FUSO_BRASIL)

    return data.astimezone(FUSO_BRASIL)


def _formatar_dh_emi(mdfe: Mdfe) -> str:
    return _data_emissao_mdfe(mdfe).strftime("%Y-%m-%dT%H:%M:%S-03:00")


def _sigla_uf(municipio: Municipio | None, fallback: str = "") -> str:
    if not municipio:
        return fallback
    return CODIGO_UF_PARA_SIGLA.get(municipio.codigo_uf, fallback)


def _buscar_municipio_por_codigo(db: Session, codigo_ibge):
    if not codigo_ibge:
        return None

    return (
        db.query(Municipio)
        .filter(Municipio.codigo_ibge == codigo_ibge)
        .first()
    )


def _buscar_municipio_empresa(db: Session, empresa) -> Municipio:
    municipio_id = _get(
        empresa,
        "municipio_id",
        "cidade_id",
        "codigo_municipio",
        "codigo_ibge",
        padrao=None,
    )

    municipio = _buscar_municipio_por_codigo(db, municipio_id)
    if not municipio:
        raise ValueError("Município da empresa não encontrado.")

    return municipio


def _buscar_municipio_transportador(db: Session, transportador):
    municipio_id = _get(transportador, "municipio_id", padrao=None)
    return _buscar_municipio_por_codigo(db, municipio_id) if municipio_id else None


def _buscar_municipios_rota(db: Session, mdfe: Mdfe):
    origem = _buscar_municipio_por_codigo(db, mdfe.rota.municipio_origem_id)
    destino = _buscar_municipio_por_codigo(db, mdfe.rota.municipio_destino_id)

    if not origem:
        raise ValueError("Município de origem da rota não encontrado.")

    if not destino:
        raise ValueError("Município de destino da rota não encontrado.")

    return origem, destino


def _buscar_placas_veiculo(db: Session, veiculo_id: int) -> list[VeiculoPlaca]:
    return (
        db.query(VeiculoPlaca)
        .filter(VeiculoPlaca.veiculo_id == veiculo_id)
        .order_by(VeiculoPlaca.id.asc())
        .all()
    )


def _buscar_placa_cavalo(placas: list[VeiculoPlaca]) -> VeiculoPlaca | None:
    for placa in placas:
        if "cavalo" in _texto(_get(placa, "descricao")).lower():
            return placa

    return placas[0] if placas else None


# -----------------------------------------------------------------------------
# Regras do emitente/transportador
# -----------------------------------------------------------------------------

def _tipo_transportador(mdfe: Mdfe) -> str:
    return _texto(_get(mdfe.transportador, "tipo_transportador")).upper()


def _transportador_e_tac(mdfe: Mdfe) -> bool:
    tipo = _tipo_transportador(mdfe)
    documento = _somente_numeros(_get(mdfe.transportador, "cpf_cnpj"))

    return (
        len(documento) == 11
        or "TAC" in tipo
        or "AUTONOMO" in tipo
        or "AUTÔNOMO" in tipo
    )


def _tp_emit(mdfe: Mdfe) -> str:
    return "2"


def _tp_prop_transportador(mdfe: Mdfe) -> str:
    return "1" if _transportador_e_tac(mdfe) else "2"


def _tp_transp(mdfe: Mdfe) -> str | None:
    return "2" if _transportador_e_tac(mdfe) else None


# -----------------------------------------------------------------------------
# Produto predominante
# -----------------------------------------------------------------------------

def _cep_valido(valor) -> str:
    cep = _somente_numeros(valor)
    return cep if len(cep) == 8 else ""


def _cep_empresa(empresa) -> str:
    cep = _cep_valido(_get(empresa, "cep"))

    if not cep:
        raise ValueError(
            "CEP da empresa inválido ou não informado. "
            "Necessário para gerar o grupo infLotacao do MDF-e."
        )

    return cep


def _cep_descarga(mdfe: Mdfe, doc: MdfeDocumento) -> str:
    cep = _cep_valido(
        _get(
            doc,
            "destinatario_cep",
            "cep_destinatario",
            "cep_descarga",
            "cep",
        )
    )

    return cep or _cep_empresa(mdfe.empresa)


def _produto_predominante(documentos: list[MdfeDocumento]) -> tuple[str, str]:
    produtos: dict[tuple[str, str], Decimal] = {}

    for doc in documentos:
        produto = _texto(
            _get(doc, "produto", "descricao_produto", "xprod"),
        ).upper()

        if not produto:
            continue

        peso = (
            getattr(doc, "peso_bruto", None)
            or getattr(doc, "peso_liquido", None)
            or Decimal("0")
        )

        ncm = _somente_numeros(_get(doc, "ncm"))
        chave = (produto[:120], ncm[:8] if len(ncm) >= 8 else "")

        produtos[chave] = produtos.get(chave, Decimal("0")) + Decimal(peso)

    if not produtos:
        return "GRAOS", ""

    return max(produtos.items(), key=lambda item: item[1])[0]


def _montar_inf_lotacao(mdfe: Mdfe, documentos: list[MdfeDocumento]) -> Element | None:
    if len(documentos) != 1:
        return None

    doc = documentos[0]
    inf_lotacao = Element("infLotacao")

    inf_local_carrega = SubElement(inf_lotacao, "infLocalCarrega")
    _add(inf_local_carrega, "CEP", _cep_empresa(mdfe.empresa))

    inf_local_descarrega = SubElement(inf_lotacao, "infLocalDescarrega")
    _add(inf_local_descarrega, "CEP", _cep_descarga(mdfe, doc))

    return inf_lotacao


def _montar_prod_pred(mdfe: Mdfe, documentos: list[MdfeDocumento]) -> Element:
    produto, ncm = _produto_predominante(documentos)

    prod_pred = Element("prodPred")
    _add(prod_pred, "tpCarga", "01")
    _add(prod_pred, "xProd", produto)

    if ncm:
        _add(prod_pred, "NCM", ncm)

    inf_lotacao = _montar_inf_lotacao(mdfe, documentos)
    if inf_lotacao is not None:
        prod_pred.append(inf_lotacao)

    return prod_pred


# -----------------------------------------------------------------------------
# Chave e grupos principais
# -----------------------------------------------------------------------------

def _garantir_chave_salva(db: Session, mdfe: Mdfe, municipio_origem: Municipio) -> dict:
    if mdfe.chave_acesso and mdfe.codigo_mdf and mdfe.digito_verificador:
        return {
            "chave": mdfe.chave_acesso,
            "cMDF": mdfe.codigo_mdf,
            "cDV": mdfe.digito_verificador,
        }

    chave_mdfe = gerar_chave_mdfe(
        cuf=municipio_origem.codigo_uf,
        data_emissao=_data_emissao_mdfe(mdfe),
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

    return chave_mdfe


def _montar_ide(
    mdfe: Mdfe,
    municipio_origem: Municipio,
    municipio_destino: Municipio,
    chave_mdfe: dict,
) -> Element:
    ide = Element("ide")

    campos = [
        ("cUF", municipio_origem.codigo_uf),
        ("tpAmb", "2"),
        ("tpEmit", _tp_emit(mdfe)),
    ]

    tp_transp = _tp_transp(mdfe)
    if tp_transp:
        campos.append(("tpTransp", tp_transp))

    campos.extend([
        ("mod", "58"),
        ("serie", mdfe.serie),
        ("nMDF", mdfe.numero),
        ("cMDF", chave_mdfe["cMDF"]),
        ("cDV", chave_mdfe["cDV"]),
        ("modal", "1"),
        ("dhEmi", _formatar_dh_emi(mdfe)),
        ("tpEmis", "1"),
        ("procEmi", "0"),
        ("verProc", VER_PROC),
        ("UFIni", _sigla_uf(municipio_origem, mdfe.uf_inicio)),
        ("UFFim", _sigla_uf(municipio_destino, mdfe.uf_fim)),
    ])

    for tag, valor in campos:
        _add(ide, tag, valor)

    inf_mun_carrega = SubElement(ide, "infMunCarrega")
    _add(inf_mun_carrega, "cMunCarrega", municipio_origem.codigo_ibge)
    _add(inf_mun_carrega, "xMunCarrega", municipio_origem.nome)

    return ide


def _montar_emitente(db: Session, empresa) -> Element:
    municipio_empresa = _buscar_municipio_empresa(db, empresa)
    emit = Element("emit")

    campos_emit = [
        ("CNPJ", _somente_numeros(_get(empresa, "cnpj", "cpf_cnpj"))),
        ("IE", _somente_numeros(_get(empresa, "inscricao_estadual", "ie", "rg_ie"))),
        ("xNome", _get(empresa, "razao_social", "nome_razao_social", "nome")),
        ("xFant", _get(empresa, "nome_fantasia", "fantasia")),
    ]

    for tag, valor in campos_emit:
        _add(emit, tag, valor)

    ender = SubElement(emit, "enderEmit")
    campos_ender = [
        ("xLgr", _get(empresa, "logradouro", "endereco")),
        ("nro", _texto(_get(empresa, "numero"), "S/N")),
        ("xBairro", _get(empresa, "bairro")),
        ("cMun", municipio_empresa.codigo_ibge),
        ("xMun", municipio_empresa.nome),
        ("CEP", _somente_numeros(_get(empresa, "cep"))),
        ("UF", _sigla_uf(municipio_empresa, _get(empresa, "estado", "uf"))),
        ("fone", _somente_numeros(_get(empresa, "telefone"))),
    ]

    for tag, valor in campos_ender:
        _add(ender, tag, valor)

    return emit


def _montar_proprietario(
    db: Session,
    elemento_pai: Element,
    mdfe: Mdfe,
    municipio_origem: Municipio,
):
    transportador = mdfe.transportador

    if not transportador:
        raise ValueError("Transportador não encontrado para montar proprietário.")

    documento = _somente_numeros(_get(transportador, "cpf_cnpj"))
    rntrc = _limpar_rntrc(_get(transportador, "rntrc"))
    nome = _texto(_get(transportador, "nome_razao_social"))

    if not documento:
        raise ValueError("CPF/CNPJ do transportador não informado.")

    if not rntrc:
        raise ValueError("RNTRC do transportador não informado.")

    if not nome:
        raise ValueError("Nome/Razão Social do transportador não informado.")

    municipio_transportador = _buscar_municipio_transportador(db, transportador)
    uf_prop = _sigla_uf(
        municipio_transportador,
        _sigla_uf(municipio_origem, mdfe.uf_inicio),
    )

    prop = SubElement(elemento_pai, "prop")
    _add(prop, "CPF" if len(documento) == 11 else "CNPJ", documento)
    _add(prop, "RNTRC", rntrc)
    _add(prop, "xNome", nome)

    ie = _somente_numeros(_get(transportador, "rg_ie"))
    if ie:
        _add(prop, "IE", ie)

    _add(prop, "UF", uf_prop)
    _add(prop, "tpProp", _tp_prop_transportador(mdfe))


def _montar_veiculo_basico(elemento: Element, placa: VeiculoPlaca, municipio_origem: Municipio, uf_fallback: str):
    _add(elemento, "cInt", placa.id)
    _add(elemento, "placa", placa.placa)
    _add(elemento, "RENAVAM", _somente_numeros(_get(placa, "renavam")))
    _add(elemento, "tara", _inteiro(_get(placa, "tara_kg")))
    _add(elemento, "capKG", _inteiro(_get(placa, "capacidade_kg")))
    _add(elemento, "capM3", _inteiro(_get(placa, "capacidade_m3")))


def _montar_rodo(db: Session, mdfe: Mdfe, municipio_origem: Municipio) -> Element:
    rodo = Element("rodo")
    veiculo = mdfe.veiculo
    motorista = mdfe.motorista

    if not mdfe.transportador:
        raise ValueError("Transportador não informado no MDF-e.")

    placas = _buscar_placas_veiculo(db, veiculo.id)
    if not placas:
        raise ValueError("O veículo selecionado não possui placas cadastradas.")

    placa_cavalo = _buscar_placa_cavalo(placas)
    if not placa_cavalo:
        raise ValueError("Não foi encontrada a placa do cavalo do veículo.")

    rntrc_transportador = _limpar_rntrc(_get(mdfe.transportador, "rntrc"))
    if not rntrc_transportador:
        raise ValueError("RNTRC do transportador não informado.")

    inf_antt = SubElement(rodo, "infANTT")
    _add(inf_antt, "RNTRC", rntrc_transportador)

    inf_contratante = SubElement(inf_antt, "infContratante")
    cnpj_emitente = _somente_numeros(_get(mdfe.empresa, "cnpj", "cpf_cnpj"))

    if cnpj_emitente:
        _add(inf_contratante, "CNPJ", cnpj_emitente)
    else:
        _add(inf_contratante, "CPF", _somente_numeros(_get(mdfe.empresa, "cpf", "cpf_cnpj")))

    veic_tracao = SubElement(rodo, "veicTracao")
    _add(veic_tracao, "cInt", veiculo.id)
    _add(veic_tracao, "placa", placa_cavalo.placa)
    _add(veic_tracao, "RENAVAM", _somente_numeros(_get(placa_cavalo, "renavam")))
    _add(veic_tracao, "tara", _inteiro(_get(placa_cavalo, "tara_kg")))
    _add(veic_tracao, "capKG", "0")
    _add(veic_tracao, "capM3", _inteiro(_get(placa_cavalo, "capacidade_m3")))

    _montar_proprietario(db, veic_tracao, mdfe, municipio_origem)

    condutor = SubElement(veic_tracao, "condutor")
    _add(condutor, "xNome", _get(motorista, "nome"))
    _add(condutor, "CPF", _somente_numeros(_get(motorista, "cpf")))

    _add(veic_tracao, "tpRod", "03")
    _add(veic_tracao, "tpCar", "00")
    _add(veic_tracao, "UF", _sigla_uf(municipio_origem, mdfe.uf_inicio))

    for placa in placas:
        descricao = _texto(_get(placa, "descricao")).lower()
        if placa.id == placa_cavalo.id or "cavalo" in descricao:
            continue

        reboque = SubElement(rodo, "veicReboque")
        _montar_veiculo_basico(reboque, placa, municipio_origem, mdfe.uf_inicio)
        _montar_proprietario(db, reboque, mdfe, municipio_origem)
        _add(reboque, "tpCar", "00")
        _add(reboque, "UF", _sigla_uf(municipio_origem, mdfe.uf_inicio))

    return rodo


def _montar_inf_modal(db: Session, mdfe: Mdfe, municipio_origem: Municipio) -> Element:
    inf_modal = Element("infModal", versaoModal=VERSAO_MODAL)
    inf_modal.append(_montar_rodo(db, mdfe, municipio_origem))
    return inf_modal


def _montar_inf_doc(documentos: list[MdfeDocumento], municipio_destino: Municipio) -> Element:
    inf_doc = Element("infDoc")
    inf_mun_descarga = SubElement(inf_doc, "infMunDescarga")

    _add(inf_mun_descarga, "cMunDescarga", municipio_destino.codigo_ibge)
    _add(inf_mun_descarga, "xMunDescarga", municipio_destino.nome)

    for doc in documentos:
        inf_nfe = SubElement(inf_mun_descarga, "infNFe")
        _add(inf_nfe, "chNFe", doc.chave_nfe)

    return inf_doc


def _montar_totais(documentos: list[MdfeDocumento]) -> Element:
    total = Element("tot")
    valor_total = sum(
        (getattr(doc, "valor_carga", None) or getattr(doc, "valor_total", None) or Decimal("0"))
        for doc in documentos
    )
    peso_total = sum((doc.peso_bruto or Decimal("0")) for doc in documentos)

    _add(total, "qNFe", len(documentos))
    _add(total, "vCarga", _decimal(valor_total, 2))
    _add(total, "cUnid", "01")
    _add(total, "qCarga", _decimal(peso_total, 4))

    return total


def _montar_inf_adic(mdfe: Mdfe) -> Element | None:
    observacoes = _get(mdfe, "observacoes", "observacao", padrao="")
    if not observacoes:
        return None

    inf_adic = Element("infAdic")
    _add(inf_adic, "infCpl", observacoes)
    return inf_adic


# -----------------------------------------------------------------------------
# Função principal
# -----------------------------------------------------------------------------

def gerar_xml_mdfe(db: Session, mdfe_id: int) -> str:
    mdfe = db.query(Mdfe).filter(Mdfe.id == mdfe_id).first()
    if not mdfe:
        raise ValueError("MDF-e não encontrado.")

    documentos = (
        db.query(MdfeDocumento)
        .filter(MdfeDocumento.mdfe_id == mdfe_id)
        .order_by(MdfeDocumento.id.asc())
        .all()
    )
    if not documentos:
        raise ValueError("Não existem NF-e vinculadas a este MDF-e.")

    municipio_origem, municipio_destino = _buscar_municipios_rota(db, mdfe)
    chave_mdfe = _garantir_chave_salva(db, mdfe, municipio_origem)

    mdfe_xml = Element("MDFe", xmlns="http://www.portalfiscal.inf.br/mdfe")
    inf_mdfe = SubElement(
        mdfe_xml,
        "infMDFe",
        versao=VERSAO_MDFE,
        Id=f"MDFe{chave_mdfe['chave']}",
    )

    grupos = [
        _montar_ide(mdfe, municipio_origem, municipio_destino, chave_mdfe),
        _montar_emitente(db, mdfe.empresa),
        _montar_inf_modal(db, mdfe, municipio_origem),
        _montar_inf_doc(documentos, municipio_destino),
        _montar_prod_pred(mdfe, documentos),
        _montar_totais(documentos),
    ]

    inf_adic = _montar_inf_adic(mdfe)
    if inf_adic is not None:
        grupos.append(inf_adic)

    for grupo in grupos:
        inf_mdfe.append(grupo)

    xml_string = _pretty_xml(mdfe_xml)

    PASTA_XML_GERADOS.mkdir(parents=True, exist_ok=True)
    caminho = PASTA_XML_GERADOS / f"mdfe_{mdfe.id}.xml"
    caminho.write_text(xml_string, encoding="utf-8")

    mdfe.xml_path = str(caminho)
    db.commit()

    return xml_string
