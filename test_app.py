
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database.database import Base, get_db
from app.database.models import User, Service, Task, Photo
from app.main import app
from app.routers import services
from app.services.auth_service import hash_password


@pytest.fixture
def test_environment(tmp_path, monkeypatch):
    """Crea una base de datos y almacenamiento temporales para cada prueba."""

    database_file = tmp_path / "test_tuhomi.db"

    test_engine = create_engine(
        f"sqlite:///{database_file.as_posix()}",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )

    TestingSessionLocal = sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=test_engine,
    )

    Base.metadata.create_all(bind=test_engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db

    # Las fotografías de prueba también se guardan fuera del proyecto.
    test_photo_dir = tmp_path / "photos"
    test_photo_dir.mkdir()
    monkeypatch.setattr(services, "PHOTO_DIR", test_photo_dir)

    db = TestingSessionLocal()

    ana = User(
        username="ana_test",
        full_name="Ana de prueba",
        password_hash=hash_password("AnaPrueba123!"),
        is_active=True,
    )
    carlos = User(
        username="carlos_test",
        full_name="Carlos de prueba",
        password_hash=hash_password("CarlosPrueba123!"),
        is_active=True,
    )

    db.add_all([ana, carlos])
    db.flush()

    ana_service = Service(
        user_id=ana.id,
        apartment="Apartamento exclusivo de Ana",
        scheduled_at=datetime(2026, 10, 22, 9, 0),
        instructions="Servicio de prueba de Ana",
        status="en progreso",
    )
    carlos_service = Service(
        user_id=carlos.id,
        apartment="Apartamento exclusivo de Carlos",
        scheduled_at=datetime(2026, 10, 22, 10, 0),
        instructions="Servicio de prueba de Carlos",
        status="en progreso",
    )

    db.add_all([ana_service, carlos_service])
    db.flush()

    ana_task = Task(
        service_id=ana_service.id,
        name="Cocina de Ana",
        is_completed=False,
    )
    carlos_task = Task(
        service_id=carlos_service.id,
        name="Cocina de Carlos",
        is_completed=False,
    )

    db.add_all([ana_task, carlos_task])
    db.flush()

    # Archivo y registro fotográfico exclusivos de Ana.
    photo_path = test_photo_dir / "foto_ana.jpg"
    photo_path.write_bytes(b"\xff\xd8\xff\xe0archivo-de-prueba")

    ana_photo = Photo(
        task_id=ana_task.id,
        filename="foto_ana.jpg",
        content_type="image/jpeg",
        size=photo_path.stat().st_size,
        path=str(photo_path.resolve()),
    )
    db.add(ana_photo)
    db.commit()

    ids = {
        "ana_service": ana_service.id,
        "carlos_service": carlos_service.id,
        "ana_task": ana_task.id,
        "carlos_task": carlos_task.id,
        "ana_photo": ana_photo.id,
    }

    db.close()

    try:
        with TestClient(app) as client:
            yield client, ids
    finally:
        app.dependency_overrides.pop(get_db, None)
        test_engine.dispose()


def login(client, username, password):
    """Inicia sesión por la ruta real de la aplicación."""
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=False,
    )


def test_health_endpoint():
    response = TestClient(app).get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["application"] == "TuHomi"


def test_home_displays_login():
    response = TestClient(app).get("/", follow_redirects=False)

    assert response.status_code == 200


def test_invalid_login_is_rejected():
    response = TestClient(app).post(
        "/login",
        data={
            "username": "usuario_inexistente_prueba",
            "password": "ClaveIncorrecta123!",
        },
        follow_redirects=False,
    )

    assert response.status_code == 303
    assert response.headers["location"] == "/?error=credenciales"


def test_service_requires_login():
    with TestClient(app) as client:
        response = client.get("/servicio", follow_redirects=False)

    assert response.status_code == 303
    assert response.headers["location"] == "/"


def test_logout_clears_session():
    with TestClient(app) as client:
        response = client.post("/logout", follow_redirects=False)

        assert response.status_code == 303
        assert response.headers["location"] == "/"

        service_response = client.get(
            "/servicio",
            follow_redirects=False,
        )

    assert service_response.status_code == 303
    assert service_response.headers["location"] == "/"


def test_ana_only_sees_her_own_service(test_environment):
    client, ids = test_environment

    response = login(client, "ana_test", "AnaPrueba123!")
    assert response.status_code == 303

    response = client.get("/servicio")

    assert response.status_code == 200
    assert "Apartamento exclusivo de Ana" in response.text
    assert "Apartamento exclusivo de Carlos" not in response.text


def test_carlos_only_sees_his_own_service(test_environment):
    client, ids = test_environment

    response = login(client, "carlos_test", "CarlosPrueba123!")
    assert response.status_code == 303

    response = client.get("/servicio")

    assert response.status_code == 200
    assert "Apartamento exclusivo de Carlos" in response.text
    assert "Apartamento exclusivo de Ana" not in response.text


def test_carlos_cannot_view_anas_photo(test_environment):
    client, ids = test_environment

    response = login(client, "carlos_test", "CarlosPrueba123!")
    assert response.status_code == 303

    response = client.get(
        f"/servicio/fotografias/{ids['ana_photo']}"
    )

    assert response.status_code == 404


def test_anonymous_user_cannot_view_photo(test_environment):
    client, ids = test_environment

    response = client.get(
        f"/servicio/fotografias/{ids['ana_photo']}"
    )

    assert response.status_code == 401


def test_carlos_cannot_complete_anas_task(test_environment):
    client, ids = test_environment

    response = login(client, "carlos_test", "CarlosPrueba123!")
    assert response.status_code == 303

    response = client.post(
        f"/servicio/tareas/{ids['ana_task']}/completar",
        files={
            "photo": (
                "prueba.jpg",
                b"\xff\xd8\xff\xe0contenido-de-prueba",
                "image/jpeg",
            )
        },
        follow_redirects=False,
    )

    assert response.status_code == 404

    # La tarea de Ana debe continuar sin completar.
    with client:
        db_dependency = app.dependency_overrides[get_db]
        db = next(db_dependency())
        try:
            task = db.query(Task).filter(
                Task.id == ids["ana_task"]
            ).first()

            assert task is not None
            assert task.is_completed is False
        finally:
            db.close()


def test_carlos_cannot_access_anas_service_by_id(test_environment):
    client, ids = test_environment

    response = login(client, "carlos_test", "CarlosPrueba123!")
    assert response.status_code == 303

    # La página solo consulta el servicio asociado a la sesión;
    # no se permite elegir un servicio mediante un ID en la URL.
    response = client.get(f"/servicio?id={ids['ana_service']}")

    assert response.status_code == 200
    assert "Apartamento exclusivo de Carlos" in response.text
    assert "Apartamento exclusivo de Ana" not in response.text
