import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL não configurado no arquivo .env")

engine = create_engine(
    DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)