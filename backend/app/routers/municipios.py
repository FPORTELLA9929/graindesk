from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.municipio import Municipio

router = APIRouter(
    prefix="/api",
    tags=["Municípios"]
)


@router.get("/municipios")
def pesquisar_municipios(
    q: str = Query(...)
    ,
    db: Session = Depends(get_db)
):
    termo = q.strip()

    if len(termo) < 2:
        return []

    municipios = (
        db.query(Municipio)
        .filter(
            Municipio.nome.ilike(f"%{termo}%")
        )
        .order_by(Municipio.nome.asc())
        .limit(20)
        .all()
    )

    return [
        {
            "codigo_ibge": municipio.codigo_ibge,
            "nome": municipio.nome,
            "codigo_uf": municipio.codigo_uf
        }
        for municipio in municipios
    ]