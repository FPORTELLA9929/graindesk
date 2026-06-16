from sqlalchemy import func
from sqlalchemy.orm import Session, aliased

from app.models.transportador import Transportador
from app.models.municipio import Municipio
from app.schemas.transportador import TransportadorCreate, TransportadorUpdate


def listar_transportadores(
    db: Session,
    busca: str | None = None,
    tipo_pessoa: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
):
    MunicipioCadastro = aliased(Municipio)

    query = (
        db.query(
            Transportador,
            MunicipioCadastro.nome.label("municipio_nome"),
            MunicipioCadastro.codigo_uf.label("municipio_uf"),
        )
        .join(MunicipioCadastro, Transportador.municipio_id == MunicipioCadastro.codigo_ibge)
    )

    if busca:
        termo = f"%{busca.strip()}%"
        query = query.filter(
            Transportador.nome_razao_social.ilike(termo)
            | Transportador.nome_fantasia.ilike(termo)
            | Transportador.cpf_cnpj.ilike(termo)
        )

    if tipo_pessoa in ["PF", "PJ"]:
        query = query.filter(Transportador.tipo_pessoa == tipo_pessoa)

    if status == "ativos":
        query = query.filter(Transportador.ativo.is_(True))
    elif status == "inativos":
        query = query.filter(Transportador.ativo.is_(False))

    page = max(page, 1)
    per_page = max(min(per_page, 100), 10)

    total = query.count()
    offset = (page - 1) * per_page

    transportadores = (
        query
        .order_by(Transportador.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page if total else 1

    return {
        "items": transportadores,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def buscar_transportador(db: Session, transportador_id: int):
    return (
        db.query(Transportador)
        .filter(Transportador.id == transportador_id)
        .first()
    )


def buscar_por_cpf_cnpj(db: Session, cpf_cnpj: str):
    documento_normalizado = cpf_cnpj.strip()

    return (
        db.query(Transportador)
        .filter(func.lower(Transportador.cpf_cnpj) == documento_normalizado.lower())
        .first()
    )


def criar_transportador(db: Session, dados: TransportadorCreate):
    transportador = Transportador(**dados.model_dump())

    db.add(transportador)
    db.commit()

    return transportador


def atualizar_transportador(
    db: Session,
    transportador: Transportador,
    dados: TransportadorUpdate,
):
    for campo, valor in dados.model_dump().items():
        setattr(transportador, campo, valor)

    db.commit()

    return transportador


def excluir_transportador(db: Session, transportador: Transportador):
    db.delete(transportador)
    db.commit()