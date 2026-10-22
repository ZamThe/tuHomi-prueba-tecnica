
import os
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware

from app.database.database import Base, engine
from app.database import models
from app.routers import auth, services

BASE_DIR = Path(__file__).resolve().parent

templates = Jinja2Templates(
    directory=str(BASE_DIR / "templates")
)

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="TuHomi",
    description="Gestión de servicios de limpieza",
    version="1.0.0",
)

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get(
        "SESSION_SECRET",
        "CLAVE-LOCAL-TEMPORAL-CAMBIAR-ANTES-DE-PRODUCCION",
    ),
    same_site="lax",
    https_only=False,
)

app.mount(
    "/static",
    StaticFiles(directory=str(BASE_DIR / "static")),
    name="static",
)

app.include_router(auth.router)
app.include_router(services.router)


@app.get("/")
def home(request: Request):
    if request.session.get("user_id"):
        return RedirectResponse(
            url="/servicio",
            status_code=303,
        )

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "error": (
                request.query_params.get("error")
                == "credenciales"
            )
        },
    )


@app.get("/health")
def health():
    return {
        "status": "ok",
        "application": "TuHomi",
    }
