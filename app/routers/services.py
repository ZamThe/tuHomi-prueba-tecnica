
from datetime import datetime
from pathlib import Path
from uuid import uuid4
import json
from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    Request,
    UploadFile,
)
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session, selectinload
from fastapi.responses import HTMLResponse
from app.database.database import get_db
from app.database.models import Photo, Service, Task, User
from fastapi.responses import HTMLResponse
from html import escape


def show_alert(message: str):
    safe_message = escape(message, quote=True)

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>TuHomi</title>
        </head>
        <body>
            <script>
                alert("{safe_message}");
                window.location.href = "/servicio";
            </script>
        </body>
        </html>
        """,
        status_code=400,
    )

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
PROJECT_DIR = BASE_DIR.parent
PHOTO_DIR = PROJECT_DIR / "storage" / "photos"

PHOTO_DIR.mkdir(parents=True, exist_ok=True)

templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

MAX_PHOTO_SIZE = 5 * 1024 * 1024

ALLOWED_TYPES = {
    "image/jpeg": (".jpg", ".jpeg"),
    "image/png": (".png",),
}


def get_current_user(request: Request, db: Session):
    """Obtiene el usuario autenticado desde la sesión."""
    user_id = request.session.get("user_id")

    if not user_id:
        return None

    user = db.query(User).filter(User.id == user_id).first()

    if user is None or not user.is_active:
        request.session.clear()
        return None

    return user


def get_user_service(db: Session, user_id: int):
    """Obtiene únicamente el servicio del usuario autenticado."""
    return (
        db.query(Service)
        .options(selectinload(Service.tasks).selectinload(Task.photo))
        .filter(Service.user_id == user_id)
        .first()
    )


def get_elapsed_seconds(service: Service) -> int:
    """Calcula el tiempo acumulado, incluyendo el tramo activo."""
    elapsed = service.accumulated_seconds or 0

    if service.status == "en progreso" and service.work_started_at:
        elapsed += max(
            0,
            int(
                (
                    datetime.utcnow() - service.work_started_at
                ).total_seconds()
            ),
        )

    return elapsed


def valid_image_signature(content_type: str, data: bytes) -> bool:
    """Comprueba la firma básica del archivo de imagen."""
    if content_type == "image/jpeg":
        return data.startswith(b"\xff\xd8\xff")

    if content_type == "image/png":
        return data.startswith(b"\x89PNG\r\n\x1a\n")

    return False

def show_alert(message: str):
    import json

    safe_message = json.dumps(message, ensure_ascii=False)

    return HTMLResponse(
        content=f"""
        <!DOCTYPE html>
        <html lang="es">
        <head>
            <meta charset="UTF-8">
            <title>TuHomi</title>
        </head>
        <body>
            <script>
                alert({safe_message});
                window.location.href = "/servicio";
            </script>
        </body>
        </html>
        """,
        status_code=400,
    )

@router.get("/servicio")
def service_page(
    request: Request,
    db: Session = Depends(get_db),
):
    """Muestra el servicio y el tiempo acumulado."""
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    service = get_user_service(db, user.id)

    timer_seconds = get_elapsed_seconds(service) if service else 0

    return templates.TemplateResponse(
        request=request,
        name="service.html",
        context={
            "user": user,
            "service": service,
            "timer_seconds": timer_seconds,
        },
    )


@router.get("/servicio/fotografias/{photo_id}")
def view_task_photo(
    photo_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Debes iniciar sesión para ver esta fotografía.",
        )

    photo = (
        db.query(Photo)
        .join(Task, Photo.task_id == Task.id)
        .join(Service, Task.service_id == Service.id)
        .filter(
            Photo.id == photo_id,
            Service.user_id == user.id,
        )
        .first()
    )

    if photo is None:
        raise HTTPException(
            status_code=404,
            detail="Fotografía no encontrada.",
        )

    path = Path(photo.path).resolve()

    if not path.is_relative_to(PHOTO_DIR.resolve()):
        raise HTTPException(
            status_code=403,
            detail="Ruta de fotografía no permitida.",
        )

    if not path.is_file():
        raise HTTPException(
            status_code=404,
            detail="El archivo de fotografía no existe.",
        )

    return FileResponse(
        path=str(path),
        media_type=photo.content_type,
        filename=photo.filename,
        content_disposition_type="inline",
    )


@router.post("/servicio/iniciar")
def start_service(
    request: Request,
    db: Session = Depends(get_db),
):
    """Inicia el servicio y su cronómetro."""
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    service = get_user_service(db, user.id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="No tienes un servicio asignado.",
        )

    if service.status != "pendiente":
        raise HTTPException(
            status_code=400,
            detail="El servicio no se puede iniciar.",
        )

    now = datetime.utcnow()

    service.status = "en progreso"
    service.started_at = now
    service.work_started_at = now
    service.accumulated_seconds = 0

    db.commit()

    return RedirectResponse("/servicio", status_code=303)


@router.post("/servicio/pausar")
def pause_service(
    request: Request,
    db: Session = Depends(get_db),
):
    """Guarda el tiempo trabajado y pausa el cronómetro."""
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    service = get_user_service(db, user.id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="No tienes un servicio asignado.",
        )

    if service.status != "en progreso" or not service.work_started_at:
        raise HTTPException(
            status_code=400,
            detail="El servicio no está activo o ya está pausado.",
        )

    now = datetime.utcnow()

    service.accumulated_seconds = get_elapsed_seconds(service)
    service.work_started_at = None
    service.status = "pausado"

    db.commit()

    return RedirectResponse("/servicio", status_code=303)


@router.post("/servicio/reanudar")
def resume_service(
    request: Request,
    db: Session = Depends(get_db),
):
    """Reanuda el cronómetro sin perder el tiempo acumulado."""
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    service = get_user_service(db, user.id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="No tienes un servicio asignado.",
        )

    if service.status != "pausado":
        raise HTTPException(
            status_code=400,
            detail="El servicio no está pausado.",
        )

    service.status = "en progreso"
    service.work_started_at = datetime.utcnow()

    db.commit()

    return RedirectResponse("/servicio", status_code=303)


@router.post("/servicio/tareas/{task_id}/completar")
async def complete_task(
    task_id: int,
    request: Request,
    photo: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """Guarda la fotografía y completa una tarea."""
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    task = (
        db.query(Task)
        .join(Service, Task.service_id == Service.id)
        .filter(
            Task.id == task_id,
            Service.user_id == user.id,
        )
        .first()
    )

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada.",
        )

    service = (
        db.query(Service)
        .filter(
            Service.id == task.service_id,
            Service.user_id == user.id,
        )
        .first()
    )

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="Servicio no encontrado.",
        )

    if service.status != "en progreso":
        raise HTTPException(
            status_code=400,
            detail="Debes tener el servicio en progreso para completar tareas.",
        )

    existing_photo = (
        db.query(Photo).filter(Photo.task_id == task.id).first()
    )

    if task.is_completed or existing_photo is not None:
        raise HTTPException(
            status_code=400,
            detail="Esta tarea ya fue completada.",
        )

    content_type = (photo.content_type or "").lower()

    if content_type not in ALLOWED_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Solo se permiten imágenes JPG o PNG.",
        )

    try:
        data = await photo.read(MAX_PHOTO_SIZE + 1)

        if not data:
            raise HTTPException(
                status_code=400,
                detail="El archivo está vacío.",
            )

        if len(data) > MAX_PHOTO_SIZE:
            raise HTTPException(
                status_code=413,
                detail="La imagen supera el límite de 5 MB.",
            )

        if not valid_image_signature(content_type, data):
            raise HTTPException(
                status_code=400,
                detail="El contenido no coincide con una imagen JPG o PNG válida.",
            )

        extension = ".jpg" if content_type == "image/jpeg" else ".png"
        filename = f"{uuid4().hex}{extension}"
        destination = PHOTO_DIR / filename

        try:
            destination.write_bytes(data)

            photo_record = Photo(
                task_id=task.id,
                filename=filename,
                content_type=content_type,
                size=len(data),
                path=str(destination.resolve()),
                uploaded_at=datetime.utcnow(),
            )

            db.add(photo_record)

            task.is_completed = True
            task.completed_at = datetime.utcnow()

            db.commit()

        except Exception:
            db.rollback()

            try:
                destination.unlink(missing_ok=True)
            except OSError:
                pass

            raise HTTPException(
                status_code=500,
                detail="No fue posible guardar la fotografía.",
            )

    finally:
        await photo.close()

    return RedirectResponse("/servicio", status_code=303)


@router.post("/servicio/finalizar")
def finish_service(
    request: Request,
    db: Session = Depends(get_db),
):
    user = get_current_user(request, db)

    if user is None:
        return RedirectResponse("/", status_code=303)

    service = get_user_service(db, user.id)

    if service is None:
        raise HTTPException(
            status_code=404,
            detail="No tienes un servicio asignado.",
        )

    if service.status != "en progreso":
        raise HTTPException(
            status_code=400,
            detail="El servicio debe estar en progreso para finalizarlo.",
        )

    tasks = db.query(Task).filter(
        Task.service_id == service.id
    ).all()

    if not tasks:
        raise HTTPException(
            status_code=400,
            detail="El servicio no tiene tareas.",
        )

    for task in tasks:
        photo = db.query(Photo).filter(
            Photo.task_id == task.id
        ).first()

        if not task.is_completed or photo is None:
            return show_alert(
               f"La tarea '{task.name}' no tiene su fotografía "
            )

        if not photo.path or not Path(photo.path).is_file():
            raise HTTPException(
                status_code=400,
                detail=(
                    f"No se encuentra el archivo de fotografía "
                    f"de la tarea '{task.name}'."
                ),
            )

    now = datetime.utcnow()

    # Añade el último tramo activo al tiempo acumulado.
    service.accumulated_seconds = get_elapsed_seconds(service)
    service.work_started_at = None
    service.status = "finalizado"
    service.finished_at = now

    db.commit()

    return RedirectResponse("/servicio", status_code=303)
