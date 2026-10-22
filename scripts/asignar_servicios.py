
from pathlib import Path
import sys

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from sqlalchemy import func
from app.database.database import SessionLocal
from app.database.models import User, Service, Task

# Tareas que se crearán para cada servicio nuevo.
TAREAS = [
    "Limpieza general",
    "Cocina",
    "Baño",
    "Habitaciones",
    "Revision final",
]


def asignar_servicios():
    db = SessionLocal()

    try:
        usuarios = (
            db.query(User)
            .filter(User.is_active.is_(True))
            .order_by(User.id)
            .all()
        )

        if len(usuarios) != 2:
            print(
                f"Se esperaban 2 usuarios activos, "
                f"pero se encontraron {len(usuarios)}."
            )
            print("No se realizaron cambios.")
            return

        print("\nUsuarios encontrados:")
        for usuario in usuarios:
            print(f"- {usuario.username} ({usuario.full_name})")

        cantidad = db.query(Service).count()

        if cantidad:
            confirmacion = input(
                f"\nHay {cantidad} servicios registrados. "
                "Se repartirán entre los dos usuarios "
                "sin cambiar los que ya tienen asignados.\n"
                "Escribe ASIGNAR para continuar: "
            )

            if confirmacion.strip() != "ASIGNAR":
                print("Operación cancelada.")
                return

            # Repartir los servicios existentes que aún no tengan usuario
            # válido, sin modificar las asignaciones actuales.
            servicios = (
                db.query(Service)
                .filter(Service.user_id.is_(None))
                .order_by(Service.id)
                .all()
            )

            for indice, servicio in enumerate(servicios):
                servicio.user_id = usuarios[indice % 2].id

            if servicios:
                db.commit()
                print(f"Servicios sin asignar distribuidos: {len(servicios)}")
            else:
                print(
                    "Todos los servicios ya tienen usuario asignado. "
                    "No se modificaron."
                )

        else:
            confirmacion = input(
                "\nNo hay servicios registrados. "
                "¿Deseas crear 2 servicios de prueba, uno por usuario? "
                "Escribe CREAR para continuar: "
            )

            if confirmacion.strip() != "CREAR":
                print("Operación cancelada.")
                return

            from datetime import datetime, timedelta

            for indice, usuario in enumerate(usuarios):
                servicio = Service(
                    user_id=usuario.id,
                    apartment=f"Apartamento de prueba {indice + 1}",
                    scheduled_at=datetime.now() + timedelta(days=indice + 1),
                    instructions="Servicio de prueba. Puedes editarlo después.",
                    status="pendiente",
                )
                db.add(servicio)
                db.flush()

                for nombre_tarea in TAREAS:
                    db.add(
                        Task(
                            service_id=servicio.id,
                            name=nombre_tarea,
                            is_completed=False,
                        )
                    )

            db.commit()
            print("Se crearon 2 servicios de prueba, uno por usuario.")

        print("\nResumen de servicios por usuario:")
        for usuario in usuarios:
            total = (
                db.query(func.count(Service.id))
                .filter(Service.user_id == usuario.id)
                .scalar()
            )
            print(f"- {usuario.username}: {total} servicio(s)")

        print("\nProceso finalizado.")

    except Exception as error:
        db.rollback()
        print(f"Error: {error}")
        print("Los cambios pendientes fueron revertidos.")

    finally:
        db.close()


if __name__ == "__main__":
    asignar_servicios()
