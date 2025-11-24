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
    try:
        if event_type in ["user.created", "user.updated"]:
            user_id = data.get("id")
            email_addresses = data.get("email_addresses", [])
            primary_email_id = data.get("primary_email_address_id")
            
            email = ""
            for email_obj in email_addresses:
                if email_obj.get("id") == primary_email_id:
                    email = email_obj.get("email_address", "")
                    break
            
            # Si no se encontró el primario, usar el primero disponible
            if not email and email_addresses:
                email = email_addresses[0].get("email_address", "")

            defaults = {
                "first_name": data.get("first_name", ""),
                "last_name": data.get("last_name", ""),
                "username": data.get("username", ""),
                "image_url": data.get("image_url", ""),
                "email": email,
            }

            User.objects.update_or_create(userid=user_id, defaults=defaults)

        elif event_type == "user.deleted":
            user_id = data.get("id")
            User.objects.filter(userid=user_id).update(is_active=False)
            

    except Exception as e:
        print(f"Error processing webhook: {e}")
        return HttpResponse(status=500)

    return HttpResponse(status=200)