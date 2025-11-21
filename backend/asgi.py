"""
ASGI config for backend project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')

django_app = get_asgi_application()

try:
    from deliveries.routing import websocket_urlpatterns
except Exception:
    import traceback
    print("Error importing deliveries.routing.websocket_urlpatterns:")
    traceback.print_exc()
    websocket_urlpatterns = []
else:
    try:
        # Mostrar las rutas WebSocket cargadas para depuración
        print("Loaded websocket_urlpatterns:")
        for p in websocket_urlpatterns:
            try:
                print(' -', getattr(p, 'pattern', p))
            except Exception:
                print(' -', p)
    except Exception:
        pass

application = ProtocolTypeRouter({
    'http': django_app,
    'websocket': AuthMiddlewareStack(URLRouter(websocket_urlpatterns)),
})
