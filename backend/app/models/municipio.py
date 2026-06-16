from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Municipio(Base):
    __tablename__ = "municipios"

    codigo_ibge: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nome: Mapped[str] = mapped_column(String(100), nullable=False, index=True)

    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)

    capital: Mapped[bool] = mapped_column(Boolean, nullable=False)
    codigo_uf: Mapped[int] = mapped_column(Integer, nullable=False, index=True)

    siafi_id: Mapped[str] = mapped_column(String(4), nullable=False, unique=True)
    ddd: Mapped[int] = mapped_column(Integer, nullable=False)
    fuso_horario: Mapped[str] = mapped_column(String(32), nullable=False)