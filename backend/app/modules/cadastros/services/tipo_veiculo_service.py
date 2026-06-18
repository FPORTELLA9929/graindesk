from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.tipo_veiculo import TipoVeiculo
from app.schemas.tipo_veiculo import TipoVeiculoCreate, TipoVeiculoUpdate


def listar_tipos_veiculo(
    db: Session,
    descricao: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
):
    query = db.query(TipoVeiculo)

    if descricao:
        query = query.filter(TipoVeiculo.descricao.ilike(f"%{descricao.strip()}%"))

    if status == "ativos":
        query = query.filter(TipoVeiculo.ativo.is_(True))
    elif status == "inativos":
        query = query.filter(TipoVeiculo.ativo.is_(False))

    page = max(page, 1)
    per_page = max(min(per_page, 100), 10)

    total = query.count()
    offset = (page - 1) * per_page

    tipos = (
        query
        .order_by(TipoVeiculo.id.desc())
        .offset(offset)
        .limit(per_page)
        .all()
    )

    total_pages = (total + per_page - 1) // per_page if total else 1

    return {
        "items": tipos,
        "total": total,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
    }


def buscar_tipo_veiculo(db: Session, tipo_veiculo_id: int):
    return (
        db.query(TipoVeiculo)
        .filter(TipoVeiculo.id == tipo_veiculo_id)
        .first()
    )


def buscar_por_descricao(db: Session, descricao: str):
    descricao_normalizada = descricao.strip().lower()

    return (
        db.query(TipoVeiculo)
        .filter(func.lower(TipoVeiculo.descricao) == descricao_normalizada)
        .first()
    )


def criar_tipo_veiculo(db: Session, dados: TipoVeiculoCreate):
    tipo_veiculo = TipoVeiculo(**dados.model_dump())

    db.add(tipo_veiculo)
    db.commit()

    return tipo_veiculo


def atualizar_tipo_veiculo(
    db: Session,
    tipo_veiculo: TipoVeiculo,
    dados: TipoVeiculoUpdate,
):
    for campo, valor in dados.model_dump().items():
        setattr(tipo_veiculo, campo, valor)

    db.commit()

    return tipo_veiculo


def excluir_tipo_veiculo(db: Session, tipo_veiculo: TipoVeiculo):
    db.delete(tipo_veiculo)
    db.commit()