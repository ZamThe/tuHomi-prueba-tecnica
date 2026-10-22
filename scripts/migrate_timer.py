
import sqlite3
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[1]
DB_PATH = PROJECT_DIR / "data" / "tuhomi.db"


def migrate():
    if not DB_PATH.exists():
        raise FileNotFoundError(
            f"No se encontró la base de datos: {DB_PATH}"
        )

    with sqlite3.connect(DB_PATH) as connection:
        columns = {
            row[1]
            for row in connection.execute(
                "PRAGMA table_info(services)"
            ).fetchall()
        }

        if "accumulated_seconds" not in columns:
            connection.execute(
                """
                ALTER TABLE services
                ADD COLUMN accumulated_seconds
                INTEGER NOT NULL DEFAULT 0
                """
            )
            print("Columna accumulated_seconds agregada.")

        if "work_started_at" not in columns:
            connection.execute(
                """
                ALTER TABLE services
                ADD COLUMN work_started_at DATETIME
                """
            )
            print("Columna work_started_at agregada.")

        connection.commit()

    print("Migración del contador terminada.")


if __name__ == "__main__":
    migrate()
