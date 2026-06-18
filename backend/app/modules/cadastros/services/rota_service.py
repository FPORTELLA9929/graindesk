from sqlalchemy.orm import Session, aliased

from app.models.rota import Rota
from app.models.municipio import Municipio
from app.schemas.rota import RotaCreate, RotaUpdate


def listar_rotas(
    db: Session,
    origem: str | None = None,
    destino: str | None = None,
    status: str | None = None,
    page: int = 1,
    per_page: int = 25,
):
    Origem = aliased(Municipio)
    Destino = aliased(Municipio)

    page = max(page or 1, 1)
    per_page = max(min(per_page or 25, 50), 10)
    offset = (page - 1) * per_page

    query = (
        db.query(
            Rota,
            Origem.nome.label("origem_nome"),
            Destino.nome.label("destino_nome"),
        )
        .join(Origem, Rota.municipio_origem_id == Origem.codigo_ibge)
        .join(Destino, Rota.municipio_destino_id == Destino.codigo_ibge)
    )

    if origem:
        query = query.filter(Origem.nome.ilike(f"%{origem.strip()}%"))

    if destino:
        query = query.filter(Destino.nome.ilike(f"%{destino.strip()}%"))

    if status == "ativas":
        query = query.filter(Rota.ativo.is_(True))
    elif status == "inativas":
        query = query.filter(Rota.ativo.is_(False))

    registros = (
        query
        .order_by(Rota.id.desc())
        .offset(offset)
        .limit(per_page + 1)
        .all()
    )

    tem_proxima = len(registros) > per_page
    rotas = registros[:per_page]

    total_estimado = offset + len(rotas)
    if tem_proxima:
        total_estimado += 1

    total_pages = page + 1 if tem_proxima else page

    return {
        "items": rotas,
        "total": total_estimado,
        "page": page,
        "per_page": per_page,
        "total_pages": total_pages,
        "tem_proxima": tem_proxima,
    }


def buscar_rota(db: Session, rota_id: int):
    return (
        db.query(Rota)
        .filter(Rota.id == rota_id)
        .first()
    )


def existe_rota_ativa_duplicada(
    db: Session,
    municipio_origem_id: int,
    municipio_destino_id: int,
    rota_id_ignorar: int | None = None,
):
    query = (
        db.query(Rota.id)
        .filter(Rota.municipio_origem_id == municipio_origem_id)
        .filter(Rota.municipio_destino_id == municipio_destino_id)
        .filter(Rota.ativo.is_(True))
    )

    if rota_id_ignorar:
        query = query.filter(Rota.id != rota_id_ignorar)

    return query.first() is not None


def criar_rota(
    db: Session,
    dados: RotaCreate,
    commit: bool = True,
):
    rota = Rota(**dados.model_dump())

    db.add(rota)

    if commit:
        db.commit()
        db.refresh(rota)
    else:
        db.flush()

    return rota


def atualizar_rota(
    db: Session,
    rota: Rota,
    dados: RotaUpdate,
    commit: bool = True,
):
    for campo, valor in dados.model_dump().items():
        setattr(rota, campo, valor)

    if commit:
        db.commit()
        db.refresh(rota)
    else:
        db.flush()

    return rota


def excluir_rota(
    db: Session,
    rota: Rota,
    commit: bool = True,
):
    db.delete(rota)

    if commit:
        db.commit()
    else:
        db.flush()