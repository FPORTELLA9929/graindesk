from sqlalchemy import func, or_
from sqlalchemy.orm import Session, aliased

from app.modules.cadastros.models.transportador import Transportador
from app.modules.cadastros.models.municipio import Municipio
from app.modules.cadastros.schemas.transportador import (
    TransportadorCreate,
    TransportadorUpdate,
)


def listar_transportadores(
    db: Session,
    busca: str | None = None,
    tipo_pessoa: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
):
    MunicipioCadastro = aliased(Municipio)

    page = max(page or 1, 1)
    per_page = max(min(per_page or 25, 50), 10)

    query = (
        db.query(
            Transportador,
            MunicipioCadastro.nome.label("municipio_nome"),
            MunicipioCadastro.codigo_uf.label("municipio_uf"),
        )
        .outerjoin(
            MunicipioCadastro,
            Transportador.municipio_id == MunicipioCadastro.codigo_ibge,
        )
    )

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            or_(
                Transportador.nome_razao_social.ilike(termo),
                Transportador.nome_fantasia.ilike(termo),
                Transportador.cpf_cnpj.ilike(termo),
                Transportador.rntrc.ilike(termo),
                Transportador.tipo_transportador.ilike(termo),
            )
        )

    if tipo_pessoa in ["PF", "PJ"]:
        query = query.filter(Transportador.tipo_pessoa == tipo_pessoa)

    if status == "ativos":
        query = query.filter(Transportador.ativo.is_(True))
    elif status == "inativos":
        query = query.filter(Transportador.ativo.is_(False))

    offset = (page - 1) * per_page

    registros = (
        query
        .order_by(Transportador.id.desc())
        .offset(offset)
        .limit(per_page + 1)
        .all()
    )

    tem_proxima = len(registros) > per_page
    transportadores = registros[:per_page]

    total_estimado = offset + len(transportadores)
    if tem_proxima:
        total_estimado += 1

    total_pages = page + 1 if tem_proxima else page

    return {
        "items": transportadores,
        "total": total_estimado,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "tem_proxima": tem_proxima,
    }


def buscar_transportador(db: Session, transportador_id: int):
    return (
        db.query(Transportador)
        .filter(Transportador.id == transportador_id)
        .first()
    )


def buscar_por_cpf_cnpj(db: Session, cpf_cnpj: str | None):
    if not cpf_cnpj:
        return None

    documento_normalizado = cpf_cnpj.strip()

    if not documento_normalizado:
        return None

    return (
        db.query(Transportador)
        .filter(func.lower(Transportador.cpf_cnpj) == documento_normalizado.lower())
        .first()
    )


def criar_transportador(
    db: Session,
    dados: TransportadorCreate,
    commit: bool = True,
):
    transportador = Transportador(**dados.model_dump())

    db.add(transportador)

    if commit:
        db.commit()
        db.refresh(transportador)
    else:
        db.flush()

    return transportador


def atualizar_transportador(
    db: Session,
    transportador: Transportador,
    dados: TransportadorUpdate,
    commit: bool = True,
):
    for campo, valor in dados.model_dump().items():
        setattr(transportador, campo, valor)

    if commit:
        db.commit()
        db.refresh(transportador)
    else:
        db.flush()

    return transportador


def excluir_transportador(
    db: Session,
    transportador: Transportador,
    commit: bool = True,
):
    db.delete(transportador)

    if commit:
        db.commit()
    else:
        db.flush()