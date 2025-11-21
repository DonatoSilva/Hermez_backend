import json
from django.conf import settings
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from svix.webhooks import Webhook, WebhookVerificationError

from .models import User


@csrf_exempt
def clerk_webhook(request):
    """
    Escucha los webhooks de Clerk para sincronizar la información del usuario.
    """
    # 1. Verificación de la firma del webhook
    try:
        wh = Webhook(settings.CLERK_WEBHOOK_SIGNING_SECRET)
        payload = wh.verify(request.body, request.headers)
    except WebhookVerificationError as e:
        return HttpResponse(status=400)
    except Exception as e:
        return HttpResponse(status=500)

    # 2. Procesamiento del evento
    event_type = payload.get("type")
    data = payload.get("data", {})

    if not event_type or not data:
        return HttpResponse(status=400)


    # 3. Lógica para cada tipo de evento
    if event_type == "user.created":
        # Lógica para crear un nuevo usuario
        pass
    elif event_type == "user.updated":
        # Lógica para actualizar un usuario existente
        pass
    elif event_type == "user.deleted":
        # Lógica para desactivar o eliminar un usuario
        pass
    elif event_type in ["organizationMembership.created", "organizationMembership.updated"]:
        # Lógica para actualizar el rol del usuario
        pass
    elif event_type == "organizationMembership.deleted":
        # Lógica para quitar el rol del usuario
        pass

    return HttpResponse(status=200)