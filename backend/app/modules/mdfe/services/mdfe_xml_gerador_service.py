from datetime import datetime, timezone, timedelta
from decimal import Decimal
from pathlib import Path
from xml.dom import minidom
from xml.etree.ElementTree import Element, SubElement, tostring

from sqlalchemy.orm import Session

from app.modules.mdfe.models.mdfe import Mdfe
from app.modules.mdfe.models.mdfe_documento import MdfeDocumento
from app.modules.mdfe.services.mdfe_chave_service import gerar_chave_mdfe
from app.modules.cadastros.models.municipio import Municipio
from app.modules.cadastros.models.veiculo import VeiculoPlaca
from app.modules.cadastros.models.tipo_veiculo import TipoVeiculo


PASTA_XML_GERADOS = Path("app/modules/mdfe/xml/gerados")

CODIGO_UF_PARA_SIGLA = {
    11: "RO", 12: "AC", 13: "AM", 14: "RR", 15: "PA", 16: "AP", 17: "TO",
    21: "MA", 22: "PI", 23: "CE", 24: "RN", 25: "PB", 26: "PE", 27: "AL",
    28: "SE", 29: "BA", 31: "MG", 32: "ES", 33: "RJ", 35: "SP",
    41: "PR", 42: "SC", 43: "RS", 50: "MS", 51: "MT", 52: "GO", 53: "DF",
}


def _somente_numeros(valor) -> str:
    if not valor:
        return ""
    return "".join(filter(str.isdigit, str(valor)))


def _texto(valor, padrao: str = "") -> str:
    if valor is None:
        return padrao
    return str(valor).strip()


def _inteiro(valor, padrao: str = "0") -> str:
    if valor is None or valor == "":
        return padrao

    try:
        return str(int(valor))
    except Exception:
        return padrao


def _decimal(valor, casas: int = 2) -> str:
    if valor is None:
        valor = Decimal("0")
    valor = Decimal(valor)
    return f"{valor:.{casas}f}"


def _pretty_xml(elemento: Element) -> str:
    bruto = tostring(elemento, encoding="utf-8")
    return minidom.parseString(bruto).toprettyxml(
        indent="    ",
        encoding="utf-8",
    ).decode("utf-8")


def _get(objeto, *campos, padrao=""):
    if objeto is None:
        return padrao

    for campo in campos:
        if hasattr(objeto, campo):
            valor = getattr(objeto, campo)
            if valor is not None:
                return valor

    return padrao


def _data_emissao_mdfe(mdfe: Mdfe) -> datetime:
    if mdfe.criado_em:
        data_emissao = mdfe.criado_em.replace(microsecond=0)
    else:
        data_emissao = datetime.now(timezone(timedelta(hours=-3))).replace(
            microsecond=0
        )

    if data_emissao.tzinfo is None:
        data_emissao = data_emissao.replace(
            tzinfo=timezone(timedelta(hours=-3))
        )

    return data_emissao.astimezone(timezone(timedelta(hours=-3)))


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


def _buscar_municipio_empresa(db: Session, empresa):
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


def _buscar_municipios_rota(db: Session, mdfe: Mdfe):
    origem = _buscar_municipio_por_codigo(
        db,
        mdfe.rota.municipio_origem_id,
    )

    destino = _buscar_municipio_por_codigo(
        db,
        mdfe.rota.municipio_destino_id,
    )

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
        descricao = _texto(_get(placa, "descricao")).lower()

        if "cavalo" in descricao:
            return placa

    if placas:
        return placas[0]

    return None


def _buscar_tipo_veiculo(db: Session, mdfe: Mdfe):
    veiculo = mdfe.veiculo

    if not veiculo:
        return None

    tipo_veiculo_id = _get(veiculo, "tipo_veiculo_id", padrao=None)

    if not tipo_veiculo_id:
        return None

    return (
        db.query(TipoVeiculo)
        .filter(TipoVeiculo.id == tipo_veiculo_id)
        .first()
    )


def _formatar_dh_emi(mdfe: Mdfe) -> str:
    data_emissao = _data_emissao_mdfe(mdfe)
    return data_emissao.strftime("%Y-%m-%dT%H:%M:%S-03:00")


def _montar_proprietario(elemento_pai: Element, placa: VeiculoPlaca):
    documento = _somente_numeros(_get(placa, "cpf_cnpj_proprietario"))

    if not documento:
        return

    prop = SubElement(elemento_pai, "prop")

    if len(documento) == 11:
        SubElement(prop, "CPF").text = documento
    else:
        SubElement(prop, "CNPJ").text = documento

    rntrc_placa = _somente_numeros(_get(placa, "rntrc"))

    if rntrc_placa:
        SubElement(prop, "RNTRC").text = rntrc_placa


def _garantir_chave_salva(
    db: Session,
    mdfe: Mdfe,
    municipio_origem: Municipio,
) -> dict:
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

    uf_inicio = _sigla_uf(municipio_origem, mdfe.uf_inicio)
    uf_fim = _sigla_uf(municipio_destino, mdfe.uf_fim)

    SubElement(ide, "cUF").text = str(municipio_origem.codigo_uf)
    SubElement(ide, "tpAmb").text = "2"
    SubElement(ide, "tpEmit").text = "2"
    SubElement(ide, "mod").text = "58"
    SubElement(ide, "serie").text = str(mdfe.serie)
    SubElement(ide, "nMDF").text = str(mdfe.numero)
    SubElement(ide, "cMDF").text = chave_mdfe["cMDF"]
    SubElement(ide, "cDV").text = chave_mdfe["cDV"]
    SubElement(ide, "modal").text = "1"
    SubElement(ide, "dhEmi").text = _formatar_dh_emi(mdfe)
    SubElement(ide, "tpEmis").text = "1"
    SubElement(ide, "procEmi").text = "0"
    SubElement(ide, "verProc").text = "GrainDesk 1.0"
    SubElement(ide, "UFIni").text = uf_inicio
    SubElement(ide, "UFFim").text = uf_fim

    inf_mun_carrega = SubElement(ide, "infMunCarrega")
    SubElement(inf_mun_carrega, "cMunCarrega").text = str(
        municipio_origem.codigo_ibge
    )
    SubElement(inf_mun_carrega, "xMunCarrega").text = _texto(
        municipio_origem.nome
    )

    return ide


def _montar_emitente(db: Session, empresa) -> Element:
    municipio_empresa = _buscar_municipio_empresa(db, empresa)

    emit = Element("emit")

    cnpj = _somente_numeros(_get(empresa, "cnpj", "cpf_cnpj"))
    ie = _somente_numeros(_get(empresa, "inscricao_estadual", "ie", "rg_ie"))

    SubElement(emit, "CNPJ").text = cnpj
    SubElement(emit, "IE").text = ie

    SubElement(emit, "xNome").text = _texto(
        _get(empresa, "razao_social", "nome_razao_social", "nome")
    )

    SubElement(emit, "xFant").text = _texto(
        _get(empresa, "nome_fantasia", "fantasia")
    )

    ender = SubElement(emit, "enderEmit")

    SubElement(ender, "xLgr").text = _texto(
        _get(empresa, "logradouro", "endereco")
    )
    SubElement(ender, "nro").text = _texto(_get(empresa, "numero"), "S/N")
    SubElement(ender, "xBairro").text = _texto(_get(empresa, "bairro"))

    SubElement(ender, "cMun").text = str(municipio_empresa.codigo_ibge)
    SubElement(ender, "xMun").text = _texto(municipio_empresa.nome)

    SubElement(ender, "CEP").text = _somente_numeros(_get(empresa, "cep"))
    SubElement(ender, "UF").text = _sigla_uf(
        municipio_empresa,
        _get(empresa, "estado", "uf"),
    )
    SubElement(ender, "fone").text = _somente_numeros(
        _get(empresa, "telefone")
    )

    return emit


def _montar_rodo(db: Session, mdfe: Mdfe, municipio_origem: Municipio) -> Element:
    rodo = Element("rodo")

    veiculo = mdfe.veiculo
    motorista = mdfe.motorista

    placas = _buscar_placas_veiculo(db, veiculo.id)

    if not placas:
        raise ValueError("O veículo selecionado não possui placas cadastradas.")

    placa_cavalo = _buscar_placa_cavalo(placas)

    if not placa_cavalo:
        raise ValueError("Não foi encontrada a placa do cavalo do veículo.")

    rntrc_cavalo = _somente_numeros(_get(placa_cavalo, "rntrc"))

    inf_antt = SubElement(rodo, "infANTT")
    SubElement(inf_antt, "RNTRC").text = rntrc_cavalo

    veic_tracao = SubElement(rodo, "veicTracao")

    SubElement(veic_tracao, "cInt").text = str(veiculo.id)
    SubElement(veic_tracao, "placa").text = _texto(placa_cavalo.placa)
    SubElement(veic_tracao, "RENAVAM").text = _somente_numeros(
        _get(placa_cavalo, "renavam")
    )
    SubElement(veic_tracao, "tara").text = _inteiro(
        _get(placa_cavalo, "tara_kg")
    )
    SubElement(veic_tracao, "capKG").text = "0"
    SubElement(veic_tracao, "capM3").text = _inteiro(
        _get(placa_cavalo, "capacidade_m3")
    )

    _montar_proprietario(veic_tracao, placa_cavalo)

    condutor = SubElement(veic_tracao, "condutor")
    SubElement(condutor, "xNome").text = _texto(_get(motorista, "nome"))
    SubElement(condutor, "CPF").text = _somente_numeros(
        _get(motorista, "cpf")
    )

    SubElement(veic_tracao, "tpRod").text = "03"
    SubElement(veic_tracao, "tpCar").text = "00"
    SubElement(veic_tracao, "UF").text = _sigla_uf(
        municipio_origem,
        mdfe.uf_inicio,
    )

    for placa in placas:
        descricao = _texto(_get(placa, "descricao")).lower()

        if placa.id == placa_cavalo.id or "cavalo" in descricao:
            continue

        reboque = SubElement(rodo, "veicReboque")

        SubElement(reboque, "cInt").text = str(placa.id)
        SubElement(reboque, "placa").text = _texto(placa.placa)
        SubElement(reboque, "RENAVAM").text = _somente_numeros(
            _get(placa, "renavam")
        )
        SubElement(reboque, "tara").text = _inteiro(_get(placa, "tara_kg"))
        SubElement(reboque, "capKG").text = _inteiro(
            _get(placa, "capacidade_kg")
        )
        SubElement(reboque, "capM3").text = _inteiro(
            _get(placa, "capacidade_m3")
        )

        _montar_proprietario(reboque, placa)

        SubElement(reboque, "tpCar").text = "00"
        SubElement(reboque, "UF").text = _sigla_uf(
            municipio_origem,
            mdfe.uf_inicio,
        )

    return rodo


def _montar_inf_modal(db: Session, mdfe: Mdfe, municipio_origem: Municipio) -> Element:
    inf_modal = Element("infModal", versaoModal="3.00")
    inf_modal.append(_montar_rodo(db, mdfe, municipio_origem))
    return inf_modal


def _montar_inf_doc(
    documentos: list[MdfeDocumento],
    municipio_destino: Municipio,
) -> Element:
    inf_doc = Element("infDoc")

    inf_mun_descarga = SubElement(inf_doc, "infMunDescarga")

    SubElement(inf_mun_descarga, "cMunDescarga").text = str(
        municipio_destino.codigo_ibge
    )
    SubElement(inf_mun_descarga, "xMunDescarga").text = _texto(
        municipio_destino.nome
    )

    for doc in documentos:
        inf_nfe = SubElement(inf_mun_descarga, "infNFe")
        SubElement(inf_nfe, "chNFe").text = _texto(doc.chave_nfe)

    return inf_doc


def _montar_totais(documentos: list[MdfeDocumento]) -> Element:
    total = Element("tot")

    qtd_nfe = len(documentos)

    valor_total = sum(
        (
            getattr(doc, "valor_carga", None)
            or getattr(doc, "valor_total", None)
            or Decimal("0")
        )
        for doc in documentos
    )
    peso_total = sum(
        (doc.peso_bruto or Decimal("0"))
        for doc in documentos
    )

    SubElement(total, "qNFe").text = str(qtd_nfe)
    SubElement(total, "vCarga").text = _decimal(valor_total, 2)
    SubElement(total, "cUnid").text = "01"
    SubElement(total, "qCarga").text = _decimal(peso_total, 4)

    return total


def _montar_inf_adic(mdfe: Mdfe) -> Element | None:
    observacoes = _get(mdfe, "observacoes", "observacao", padrao="")

    if not observacoes:
        return None

    inf_adic = Element("infAdic")
    SubElement(inf_adic, "infCpl").text = observacoes

    return inf_adic


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

    chave_mdfe = _garantir_chave_salva(
        db=db,
        mdfe=mdfe,
        municipio_origem=municipio_origem,
    )

    mdfe_xml = Element("MDFe", xmlns="http://www.portalfiscal.inf.br/mdfe")

    inf_mdfe = SubElement(
        mdfe_xml,
        "infMDFe",
        versao="3.00",
        Id=f"MDFe{chave_mdfe['chave']}",
    )

    inf_mdfe.append(
        _montar_ide(
            mdfe=mdfe,
            municipio_origem=municipio_origem,
            municipio_destino=municipio_destino,
            chave_mdfe=chave_mdfe,
        )
    )
    inf_mdfe.append(_montar_emitente(db, mdfe.empresa))
    inf_mdfe.append(_montar_inf_modal(db, mdfe, municipio_origem))
    inf_mdfe.append(_montar_inf_doc(documentos, municipio_destino))
    inf_mdfe.append(_montar_totais(documentos))

    inf_adic = _montar_inf_adic(mdfe)

    if inf_adic is not None:
        inf_mdfe.append(inf_adic)

    xml_string = _pretty_xml(mdfe_xml)

    PASTA_XML_GERADOS.mkdir(parents=True, exist_ok=True)

    nome_arquivo = f"mdfe_{mdfe.id}.xml"
    caminho = PASTA_XML_GERADOS / nome_arquivo

    with open(caminho, "w", encoding="utf-8") as arquivo:
        arquivo.write(xml_string)

    mdfe.xml_path = str(caminho)
    db.commit()

    return xml_string