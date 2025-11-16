# Guía de Despliegue para el Backend de Hermez

Este documento describe los pasos necesarios para desplegar el proyecto en una plataforma de nube moderna que soporte aplicaciones Python y servicios de larga duración (para WebSockets).

## Resumen de la Arquitectura en Producción

- **Servidor de Aplicación (Web Service):** Un proceso ejecutará la aplicación Django usando `gunicorn` para atender las peticiones HTTP.
- **Trabajador de Fondo (Background Worker):** Un proceso separado ejecutará los consumidores de `django-channels` para manejar las conexiones WebSocket.
- **Base de Datos:** Se utilizará una base de datos PostgreSQL gestionada por la plataforma.
- **Caché/Broker de Mensajes:** Se usará un servicio de Redis para comunicar la aplicación Django con los trabajadores de `channels`.

---

## Paso 1: Preparar el Código para Producción

Estos cambios deben realizarse en tu repositorio local antes de desplegar.

### 1.1. Actualizar `requirements.txt`

Asegúrate de que tu archivo `requirements.txt` contenga las siguientes librerías, que son necesarias para un entorno de producción:

```
# Servidor de aplicación para producción
gunicorn

# Adaptador de Python para PostgreSQL
psycopg2-binary

# Servir archivos estáticos (para el admin de Django)
whitenoise

# Para leer variables de entorno de un archivo .env en desarrollo local
python-dotenv

# Para parsear la URL de la base de datos
dj-database-url
```

Puedes añadirlas al final de tu `requirements.txt`.

### 1.2. Modificar `backend/settings.py` para Producción

Es crucial no tener secretos (como la `SECRET_KEY`) directamente en el código. Usaremos variables de entorno para gestionarlos.

**A. Importar `os` y `dotenv`:**
Al principio del archivo, importa la librería `os` para acceder a las variables de entorno.

```python
import os
from pathlib import Path
# Opcional: para cargar un archivo .env en desarrollo
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Cargar variables de entorno desde .env (solo para desarrollo local)
load_dotenv(os.path.join(BASE_DIR, ".env"))
```

**B. Configurar `SECRET_KEY` y `DEBUG`:**
Reemplaza la configuración actual de `SECRET_KEY` y `DEBUG` por esto:

```python
# Lee la SECRET_KEY desde una variable de entorno.
SECRET_KEY = os.environ.get('SECRET_KEY', 'una-clave-secreta-por-defecto-para-desarrollo')

# El modo DEBUG debe ser False en producción.
# La variable de entorno se debe establecer como 'True' o 'False' (texto).
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
```

**C. Configurar `ALLOWED_HOSTS`:**
Esta configuración es vital para la seguridad. Permite que solo tu dominio de producción acceda a la aplicación.

```python
# Obtiene el dominio de una variable de entorno.
# En la plataforma de despliegue, deberás configurar la variable DEPLOYMENT_HOST con el dominio que te asignen (ej: mi-app.onrender.com)
ALLOWED_HOSTS = []
DEPLOYMENT_HOST = os.environ.get('DEPLOYMENT_HOST')
if DEPLOYMENT_HOST:
    ALLOWED_HOSTS.append(DEPLOYMENT_HOST)
```

**D. Configurar la Base de Datos (PostgreSQL):**
Reemplaza la configuración de `DATABASES` para que use PostgreSQL. La URL de conexión se leerá de una variable de entorno.

```python
import dj_database_url

DATABASES = {
    'default': dj_database_url.config(
        # La variable de entorno DATABASE_URL será proporcionada por la plataforma de despliegue.
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600
    )
}
```

**E. Configurar Archivos Estáticos con `WhiteNoise` (Recomendado):**
Esto es necesario para que el panel de administrador de Django (`/admin`) funcione correctamente.

-   Añade `whitenoise.middleware.WhiteNoiseMiddleware` a tu lista de `MIDDLEWARE`, justo después de `SecurityMiddleware`:

    ```python
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        # ... el resto de tus middlewares
    ]
    ```

-   Al final del archivo, añade la configuración para los archivos estáticos:

    ```python
    # Directorio donde `collectstatic` reunirá todos los archivos estáticos.
    STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
    STATIC_URL = '/static/'
    # Almacenamiento para los archivos estáticos
    STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
    ```

**F. Configurar `django-channels` con Redis:**
Reemplaza la configuración de `CHANNEL_LAYERS` para que use Redis en producción.

```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            # La variable de entorno REDIS_URL será proporcionada por la plataforma.
            "hosts": [os.environ.get('REDIS_URL', 'redis://localhost:6379')],
        },
    },
}
```

### 1.3. Crear un archivo `.env` para desarrollo local (Opcional)

En la raíz de tu proyecto, crea un archivo llamado `.env` (y añádelo a tu `.gitignore`). Este archivo te permitirá simular las variables de entorno en tu máquina local.

```
# .env
SECRET_KEY=tu-clave-secreta-local
DEBUG=True
# No necesitas DATABASE_URL si usas sqlite localmente
# No necesitas REDIS_URL si usas InMemoryChannelLayer localmente
```

---

## Paso 2: Configuración en la Plataforma de Despliegue

Estos son los pasos generales que seguirías en la interfaz de la plataforma de despliegue.

### 2.1. Crear los Servicios

Necesitarás crear tres servicios:
1.  **Una Base de Datos PostgreSQL:** Créala desde el panel de la plataforma. Una vez creada, te proporcionará una **URL de conexión interna**.
2.  **Un Servicio de Redis:** Créalo también desde el panel. Te dará una **URL de Redis**.
3.  **Un Servicio Web (Web Service) para la aplicación Django.**

### 2.2. Configurar el Servicio Web

1.  **Conectar Repositorio:** Conecta tu repositorio de Git (GitHub, GitLab, etc.).
2.  **Configuración Básica:**
    -   **Entorno de ejecución:** Python
    -   **Rama:** `main` (o la que uses)
    -   **Comando de Build:** `pip install -r requirements.txt \u0026\u0026 python manage.py collectstatic --no-input \u0026\u0026 python manage.py migrate`
        -   `pip install`: Instala las dependencias.
        -   `collectstatic`: Reúne todos los archivos estáticos en el directorio `STATIC_ROOT` para que `WhiteNoise` los sirva.
        -   `migrate`: Aplica las migraciones a la base de datos de producción.
    -   **Comando de Inicio:** `gunicorn backend.wsgi:application`
3.  **Variables de Entorno:**
    Aquí es donde debes añadir los secretos. Ve a la sección de "Environment" o "Variables" y añade las siguientes claves y valores:
    -   `SECRET_KEY`: Genera una nueva clave secreta segura para producción.
    -   `DATABASE_URL`: Pega la URL de conexión interna de la base de datos PostgreSQL que creaste.
    -   `REDIS_URL`: Pega la URL del servicio de Redis.
    -   `DEPLOYMENT_HOST`: El dominio que la plataforma te asigne (ej: `hermez-backend.onrender.com`).
    -   `PYTHON_VERSION`: `3.13.2`
    -   `CLERK_WEBHOOK_SIGNING_SECRET`: Tu secreto de webhook de Clerk para producción.
    -   `CORS_ALLOWED_ORIGINS`: La URL de tu frontend en producción (ej: `https://mi-frontend.vercel.app`).

### 2.3. Configurar el Trabajador de Fondo (Background Worker)

1.  **Crear un nuevo "Background Worker"** asociado a la misma aplicación.
2.  **Configuración Básica:**
    -   Heredará la configuración de build y las variables de entorno del Servicio Web.
    -   **Comando de Inicio:** `python manage.py runworker -v 2`
        -   Este comando le dice a `django-channels` que empiece a escuchar por mensajes en la capa de Redis y ejecute los consumidores correspondientes.

---

## Paso 3: Despliegue Final

Una vez que todo esté configurado, guarda los cambios. La plataforma debería empezar a construir y desplegar tus servicios automáticamente. Si todo va bien, tu API estará en línea en la URL proporcionada, y los WebSockets estarán funcionando a través del trabajador de fondo.