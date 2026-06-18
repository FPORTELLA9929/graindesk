from sqlalchemy import or_
from sqlalchemy.orm import Session, aliased

from app.models.veiculo import Veiculo, VeiculoPlaca
from app.models.transportador import Transportador
from app.models.tipo_veiculo import TipoVeiculo

from app.schemas.veiculo import VeiculoCreate, VeiculoUpdate


def montar_placas_dict(placas):
    resultado = {
        "placa_cavalo": "",
        "placa_carreta_1": "",
        "placa_dolly": "",
        "placa_carreta_2": "",
    }

    for placa in placas:
        descricao = (placa.descricao or "").upper()

        if "CAVALO" in descricao:
            resultado["placa_cavalo"] = placa.placa
        elif "DOLLY" in descricao:
            resultado["placa_dolly"] = placa.placa
        elif "CARRETA 1" in descricao:
            resultado["placa_carreta_1"] = placa.placa
        elif "CARRETA 2" in descricao:
            resultado["placa_carreta_2"] = placa.placa

    return resultado


def listar_veiculos(
    db: Session,
    busca: str | None = None,
    tipo_veiculo_id: int | None = None,
    status: str | None = None,
):
    TransportadorAlias = aliased(Transportador)
    TipoAlias = aliased(TipoVeiculo)

    query = (
        db.query(
            Veiculo,
            TransportadorAlias.nome_razao_social.label("transportador_nome"),
            TipoAlias.descricao.label("tipo_nome"),
        )
        .join(TransportadorAlias, Veiculo.transportador_id == TransportadorAlias.id)
        .join(TipoAlias, Veiculo.tipo_veiculo_id == TipoAlias.id)
    )

    if busca:
        termo = f"%{busca.strip()}%"
        query = (
            query.outerjoin(VeiculoPlaca, Veiculo.id == VeiculoPlaca.veiculo_id)
            .filter(
                or_(
                    TransportadorAlias.nome_razao_social.ilike(termo),
                    TipoAlias.descricao.ilike(termo),
                    VeiculoPlaca.placa.ilike(termo),
                )
            )
        )

    if tipo_veiculo_id:
        query = query.filter(Veiculo.tipo_veiculo_id == tipo_veiculo_id)

    if status == "ativo":
        query = query.filter(Veiculo.ativo.is_(True))
    elif status == "inativo":
        query = query.filter(Veiculo.ativo.is_(False))

    registros = (
        query
        .order_by(Veiculo.id.desc())
        .distinct()
        .limit(100)
        .all()
    )

    veiculo_ids = [registro[0].id for registro in registros]

    placas_por_veiculo = {}

    if veiculo_ids:
        placas = (
            db.query(VeiculoPlaca)
            .filter(VeiculoPlaca.veiculo_id.in_(veiculo_ids))
            .order_by(VeiculoPlaca.veiculo_id.asc(), VeiculoPlaca.id.asc())
            .all()
        )

        for placa in placas:
            placas_por_veiculo.setdefault(placa.veiculo_id, []).append(placa)

    itens = []

    for registro in registros:
        veiculo = registro[0]
        placas_dict = montar_placas_dict(placas_por_veiculo.get(veiculo.id, []))

        itens.append(
            {
                "veiculo": veiculo,
                "transportador_nome": registro.transportador_nome,
                "tipo_nome": registro.tipo_nome,
                "placa_cavalo": placas_dict["placa_cavalo"],
                "placa_carreta_1": placas_dict["placa_carreta_1"],
                "placa_dolly": placas_dict["placa_dolly"],
                "placa_carreta_2": placas_dict["placa_carreta_2"],
            }
        )

    return itens


def buscar_veiculo(db: Session, veiculo_id: int):
    return (
        db.query(Veiculo)
        .filter(Veiculo.id == veiculo_id)
        .first()
    )


def buscar_placas_veiculo(db: Session, veiculo_id: int):
    return (
        db.query(VeiculoPlaca)
        .filter(VeiculoPlaca.veiculo_id == veiculo_id)
        .order_by(VeiculoPlaca.id.asc())
        .all()
    )


def criar_veiculo(
    db: Session,
    dados: VeiculoCreate,
    commit: bool = True,
):
    veiculo = Veiculo(**dados.model_dump())

    db.add(veiculo)

    if commit:
        db.commit()
        db.refresh(veiculo)
    else:
        db.flush()

    return veiculo


def criar_placa(
    db: Session,
    veiculo_id: int,
    descricao: str,
    placa: str,
    cpf_cnpj_proprietario: str | None,
    rntrc: str | None,
    commit: bool = True,
):
    placa_obj = VeiculoPlaca(
        veiculo_id=veiculo_id,
        descricao=descricao,
        placa=placa.upper().strip(),
        cpf_cnpj_proprietario=cpf_cnpj_proprietario,
        rntrc=rntrc,
    )

    db.add(placa_obj)

    if commit:
        db.commit()
        db.refresh(placa_obj)
    else:
        db.flush()

    return placa_obj


def criar_varias_placas(
    db: Session,
    veiculo_id: int,
    placas: list[dict],
    commit: bool = True,
):
    objetos = []

    for item in placas:
        objetos.append(
            VeiculoPlaca(
                veiculo_id=veiculo_id,
                descricao=item["descricao"],
                placa=item["placa"].upper().strip(),
                cpf_cnpj_proprietario=item.get("cpf_cnpj_proprietario"),
                rntrc=item.get("rntrc"),
            )
        )

    if objetos:
        db.add_all(objetos)

    if commit:
        db.commit()
        for objeto in objetos:
            db.refresh(objeto)
    else:
        db.flush()

    return objetos


def atualizar_veiculo(
    db: Session,
    veiculo: Veiculo,
    dados: VeiculoUpdate,
    commit: bool = True,
):
    for campo, valor in dados.model_dump().items():
        setattr(veiculo, campo, valor)

    if commit:
        db.commit()
        db.refresh(veiculo)
    else:
        db.flush()

    return veiculo


def excluir_placas_veiculo(
    db: Session,
    veiculo_id: int,
    commit: bool = True,
):
    (
        db.query(VeiculoPlaca)
        .filter(VeiculoPlaca.veiculo_id == veiculo_id)
        .delete(synchronize_session=False)
    )

    if commit:
        db.commit()
    else:
        db.flush()


def excluir_veiculo(
    db: Session,
    veiculo: Veiculo,
    commit: bool = True,
):
    excluir_placas_veiculo(
        db=db,
        veiculo_id=veiculo.id,
        commit=False,
    )

    db.delete(veiculo)

    if commit:
        db.commit()
    else:
        db.flush()