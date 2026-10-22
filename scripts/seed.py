
import sys
from pathlib import Path
from datetime import datetime
from app.database.database import Base, SessionLocal, engine
from app.database import models
from app.services.auth_service import hash_password

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))



Base.metadata.create_all(bind=engine)


USERS = [
    {
        "username": "ana",
        "full_name": "Ana Martínez",
        "password": "TuHomi123!",
        "apartment": "Apartamento 301",
        "instructions": "Realizar limpieza general del apartamento.",
    },
    {
        "username": "carlos",
        "full_name": "Carlos Rodríguez",
        "password": "TuHomi456!",
        "apartment": "Apartamento 502",
        "instructions": "Realizar limpieza según las tareas asignadas.",
    },
]

TASK_NAMES = ["Cocina", "Baño", "Habitación"]


def seed_database():
    db = SessionLocal()

    try:
        for data in USERS:
            user = (
                db.query(models.User)
                .filter_by(username=data["username"])
                .first()
            )

            if user is None:
                user = models.User(
                    username=data["username"],
                    full_name=data["full_name"],
                    password_hash=hash_password(data["password"]),
                    is_active=True,
                )
                db.add(user)
                db.flush()
                print(f"Usuario creado: {user.username}")
            else:
                print(f"El usuario ya existe: {user.username}")

            service = (
                db.query(models.Service)
                .filter_by(user_id=user.id)
                .first()
            )

            if service is None:
                service = models.Service(
                    user_id=user.id,
                    apartment=data["apartment"],
                    scheduled_at=datetime.now(),
                    instructions=data["instructions"],
                    status="pendiente",
                )
                db.add(service)
                db.flush()
                print(f"Servicio creado para {user.username}")

            existing_tasks = {
                task.name
                for task in db.query(models.Task)
                .filter_by(service_id=service.id)
                .all()
            }

            for task_name in TASK_NAMES:
                if task_name not in existing_tasks:
                    db.add(
                        models.Task(
                            service_id=service.id,
                            name=task_name,
                            is_completed=False,
                        )
                    )

        db.commit()
        print("\nDatos de prueba creados correctamente.")

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
