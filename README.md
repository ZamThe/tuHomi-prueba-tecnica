# TuHomi — Prueba técnica

## 1. Descripción

TuHomi es una aplicación web para gestionar servicios de limpieza. Permite a cada usuario consultar su servicio asignado, iniciar la ejecución, completar tareas con evidencia fotográfica y finalizar el servicio cuando se cumplen las condiciones establecidas.

## 2. Tecnologías

- Python
- FastAPI
- SQLAlchemy
- SQLite
- HTML, CSS y JavaScript
- Jinja2 para las plantillas
- Pytest y FastAPI TestClient para las pruebas automatizadas

## 3. Funcionalidades

- Inicio y cierre de sesión.
- Autenticación mediante contraseñas protegidas con PBKDF2-SHA256.
- Acceso restringido al servicio asignado a cada usuario.
- Estados del servicio: pendiente, en progreso y finalizado.
- Registro de tareas completadas.
- Carga de fotografías JPG y PNG.
- Validación del tipo, contenido y tamaño de las imágenes.
- Almacenamiento local de fotografías.
- Protección del acceso a las fotografías según el usuario autenticado.
- Finalización condicionada a que todas las tareas tengan su evidencia correspondiente.

## 4. Requisitos

Se necesita Python, acceso a una terminal y las dependencias del proyecto.

## 5. Instalación

Abre PowerShell en la carpeta raíz del proyecto.

Si el proyecto incluye `requirements.txt`, instala las dependencias con:

```powershell
python -m pip install -r requirements.txt
```

Si no existe ese archivo, identifica e instala las dependencias necesarias antes de ejecutar la aplicación.

## 6. Ejecución

Desde la carpeta raíz del proyecto, ejecuta:

```powershell
python -m uvicorn app.main:app --reload
```

Abre en el navegador:

- Aplicación: http://127.0.0.1:8000
- Documentación interactiva de la API: http://127.0.0.1:8000/docs
- Estado de la aplicación: http://127.0.0.1:8000/health

Para detener el servidor, utiliza `Ctrl + C` en la terminal.

## 7. Usuarios de demostración

| Usuario | Contraseña |
|---|---|
| ana | TuHomi123! |
| carlos | TuHomi456! |

Estas credenciales son para la demostración local. No deben utilizarse en un entorno de producción.

## 8. Base de datos y fotografías

La aplicación utiliza la base de datos SQLite ubicada en `data/tuhomi.db`.

Las fotografías se almacenan localmente en `storage/photos/`. Debe verificarse que las carpetas y los permisos necesarios estén disponibles al ejecutar el proyecto.

## 9. Pruebas automatizadas

Ejecuta:

```powershell
python -m pytest -v test_app.py
```

En la ejecución reportada durante el desarrollo se aprobaron 11 pruebas relacionadas con autenticación, aislamiento entre usuarios, acceso a fotografías y protección de tareas.

Este resultado corresponde a los escenarios cubiertos por las pruebas existentes y no constituye una garantía de ausencia total de vulnerabilidades.

## 10. Consideraciones de seguridad

- Cada usuario solo debe acceder a su propio servicio.
- El acceso a fotografías requiere autenticación y validación de propiedad.
- La clave de sesión debe configurarse mediante una variable de entorno segura antes de desplegar la aplicación.


## 11. Estado de la entrega

Proyecto desarrollado y probado localmente. Antes de la entrega definitiva se deben comprobar las dependencias, la configuración de ejecución, la inicialización de los datos y la ausencia de secretos o archivos privados innecesarios.
