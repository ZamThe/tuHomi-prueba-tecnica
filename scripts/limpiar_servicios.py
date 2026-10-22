
from pathlib import Path
import sys

# Permite importar la aplicación al ejecutar este archivo desde scripts.
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from app.database.database import SessionLocal
from app.database.models import Service, Task, Photo


def limpiar_servicios():
    confirmacion = input(
        "\nATENCION: Se eliminaran todos los servicios, tareas "
        "y registros de fotografias.\n"
        "Los usuarios se conservaran.\n\n"
        "Escribe BORRAR para confirmar: "
    )

    if confirmacion.strip() != "BORRAR":
        print("\nOperacion cancelada. No se elimino informacion.")
        return

    db = SessionLocal()

    try:
        # Obtener las rutas de las evidencias antes de eliminar los registros.
        fotografias = db.query(Photo).all()
        rutas = [foto.path for foto in fotografias if foto.path]

        total_servicios = db.query(Service).count()
        total_tareas = db.query(Task).count()
        total_fotos = len(fotografias)

        # Eliminar los servicios individualmente para activar las relaciones
        # cascade de SQLAlchemy y eliminar sus tareas y fotografias.
        servicios = db.query(Service).all()

        for servicio in servicios:
            db.delete(servicio)

        db.commit()

        # Borrar los archivos fisicos de las evidencias, si existen.
        archivos_eliminados = 0

        for ruta in rutas:
            archivo = Path(ruta)

            if not archivo.is_absolute():
                archivo = BASE_DIR / archivo

            try:
                if archivo.is_file():
                    archivo.unlink()
                    archivos_eliminados += 1
            except OSError as error:
                print(f"No se pudo borrar el archivo {archivo}: {error}")

        print("\nLimpieza completada correctamente.")
        print(f"Servicios eliminados: {total_servicios}")
        print(f"Tareas eliminadas: {total_tareas}")
        print(f"Registros de fotografias eliminados: {total_fotos}")
        print(f"Archivos de evidencia eliminados: {archivos_eliminados}")
        print("Usuarios conservados: si")

    except Exception as error:
        db.rollback()
        print(f"\nError durante la limpieza: {error}")
        print("Se intento revertir los cambios en la base de datos.")

    finally:
        db.close()


if __name__ == "__main__":
    limpiar_servicios()
