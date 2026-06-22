import unicodedata

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.modules.cadastros.models.municipio import Municipio


router = APIRouter(
    prefix="/api",
    tags=["Municípios"]
)


def remover_acentos(texto: str) -> str:
    return "".join(
        caractere
        for caractere in unicodedata.normalize("NFD", texto)
        if unicodedata.category(caractere) != "Mn"
    )


@router.get("/municipios")
def pesquisar_municipios(
    q: str = Query(...),
    db: Session = Depends(get_db),
):
    termo = remover_acentos(q.strip())

    if len(termo) < 2:
        return []

    municipios = (
        db.query(Municipio)
        .filter(
            func.unaccent(Municipio.nome).ilike(
                f"%{termo}%"
            )
        )
        .order_by(Municipio.nome.asc())
        .limit(20)
        .all()
    )

    return [
        {
            "codigo_ibge": municipio.codigo_ibge,
            "nome": municipio.nome,
            "codigo_uf": municipio.codigo_uf,
        }
        for municipio in municipios
    ]