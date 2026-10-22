
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

BASE_DIR = Path(__file__).resolve().parents[2]

# Archivo de base de datos SQLite
DATA_DIR = BASE_DIR / "data"
DATA_DIR.mkdir(parents=True, exist_ok=True)

DATABASE_URL = f"sqlite:///{(DATA_DIR / 'tuhomi.db').as_posix()}"

# Conexión a SQLite
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# Sesiones para consultar y guardar información
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Clase base para los modelos
class Base(DeclarativeBase):
    pass


# Dependencia para utilizar la base de datos en las rutas
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
