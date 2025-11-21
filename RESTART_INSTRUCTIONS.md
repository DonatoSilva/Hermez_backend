# Instrucciones para reiniciar el entorno (WSL2 + Redis) y levantar el servidor ASGI en Windows

## Resumen rápido

- Redis corre en WSL2 (Ubuntu).
- El servidor ASGI (Django + Channels) se ejecuta desde PowerShell usando el `venv` de Windows.

## Pre-requisitos

- Tener WSL2 instalado y una distro (ej. Ubuntu).
- Tener el virtualenv del proyecto activable en Windows (`.venv`).
- Haber configurado `CHANNEL_LAYERS` en `backend/settings.py` para apuntar a `127.0.0.1:6379` (Redis).

## 1) Arrancar WSL y Redis

En PowerShell:

```powershell
wsl
```

En la shell de WSL (Ubuntu):

```bash
sudo service redis-server start
redis-cli ping   # debe responder: PONG
```

**Notas**:

- Si `redis-cli ping` devuelve `PONG`, Redis está listo.
- Si usaste Docker para Redis: `docker start <container>` o `docker run -d --name hermez-redis -p 6379:6379 redis:7`.

## 2) Arrancar el servidor ASGI desde Windows (PowerShell)

Abrir PowerShell en la raíz del proyecto y activar el venv de Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Arrancar con Daphne (recomendado con Channels):

```powershell
.\.venv\Scripts\python -m daphne backend.asgi:application -p 8000
```

O con Uvicorn (asegúrate de tener websockets/wsproto o `uvicorn[standard]`):

```powershell
.\.venv\Scripts\python -m uvicorn backend.asgi:application --port 8000
```

## 3) Verificaciones rápidas

- Comprobar que Redis es accesible desde Windows:

```powershell
Test-NetConnection -ComputerName 127.0.0.1 -Port 6379
```

- Probar la ruta HTTP/WS:

```powershell
curl http://localhost:8000/deliveries/api/quotes/
# y para WS (cliente):
# npm i -g wscat
# wscat -c "ws://localhost:8000/ws/deliveries/new-quotes/"
```

- Probar envío de prueba a grupo Channels desde Django shell:

```powershell
.\.venv\Scripts\python manage.py shell
```

Dentro del shell:

```python
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
cl = get_channel_layer()
async_to_sync(cl.group_send)("new_quotes", {"type":"broadcast","data":{"type":"test","payload":{"ok":True}}})
```

## 4) Iniciar en segundo plano (opcional)

Usar `Start-Process` para ejecutar el servidor en background desde PowerShell:

```powershell
Start-Process -NoNewWindow -FilePath .\.venv\Scripts\python -ArgumentList '-m','daphne','backend.asgi:application','-p','8000'
```

Para detener el proceso (buscar PID y matar):

```powershell
netstat -ano | findstr :8000
Stop-Process -Id <PID>
```

## 5) Consideraciones y troubleshooting

- Si ves `Unsupported upgrade request` o `No supported WebSocket library detected` al arrancar uvicorn, instala las extras:

```powershell
pip install "uvicorn[standard]"
# o pip install websockets wsproto
```

- Asegúrate de que `deliveries.signals` está importado en `deliveries.apps.ready()` para que los `post_save` envíen `group_send`.
- Si usas Redis en WSL y ejecutas Django en Windows y hay problemas de conexión, ejecutar Django desde WSL evita posibles problemas de red entre entornos.
- Logs útiles: conserva la ventana de PowerShell abierta para ver errores/advertencias del ASGI server.

## 6) Checklist rápido después del reinicio

- [ ] Iniciar WSL
- [ ] `sudo service redis-server start` (WSL)
- [ ] `redis-cli ping` → PONG (WSL)
- [ ] Activar `.venv` en PowerShell
- [ ] `pip install -r requirements.txt` (si instalaste algo nuevo)
- [ ] Iniciar `daphne` o `uvicorn` desde el venv
- [ ] Conectar cliente WS y probar `group_send` desde shell

---

Si quieres, también puedo generar un script `scripts/start-dev.ps1` que automatice (activar venv y arrancar daphne). ¿Lo genero ahora?
