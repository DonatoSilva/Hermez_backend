from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from .models import DeliveryQuote, DeliveryOffer, Delivery
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliverySerializer
import json

# Authentication helpers: try to support DRF Token and SimpleJWT if available
try:
    from rest_framework.authtoken.models import Token as DRFToken
except Exception:
    DRFToken = None

try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except Exception:
    JWTAuthentication = None

IN_PROGRESS_STATUSES = {'assigned', 'picked_up', 'in_transit'}


class DeliveryConsumer(JsonWebsocketConsumer):
    def connect(self):
        # Intentar autenticar usando token pasado como subprotocol ('Bearer <token>')
        import re
        subprotocols = self.scope.get('subprotocols') or []
        token_key = None
        matched_subprotocol = None

        for sp in subprotocols:
            if not isinstance(sp, str):
                continue
            # Buscar prefijos tipo Bearer( ,:,_,-)token
            m = re.match(r'^(?:Bearer[ _:-]?)(.+)$', sp)
            if m:
                token_key = m.group(1)
                matched_subprotocol = sp
                break
            # Si parece un JWT (contiene puntos) o es una cadena larga, tomarla como token crudo
            if '.' in sp or len(sp) > 40:
                token_key = sp
                matched_subprotocol = sp
                break

        # Extraer tipo de grupo (quote/delivery/new_quotes) desde la ruta para decisiones de auth
        self.group_type = self.scope.get('url_route', {}).get('kwargs', {}).get('group_type')

        if token_key:
            user = None
            # Try project-specific ClerkAuthentication first (shared logic with DRF)
            try:
                from users.authentication import ClerkAuthentication
                class _FakeRequest:
                    def __init__(self, token):
                        self.headers = {'Authorization': f'Bearer {token}'}

                try:
                    clerk_auth = ClerkAuthentication()
                    auth_result = clerk_auth.authenticate(_FakeRequest(token_key))
                    try:
                        pass
                    except Exception:
                        pass
                    if auth_result:
                        user = auth_result[0]
                except Exception as exc:
                    try:
                        pass
                    except Exception:
                        pass
                    user = None
            except Exception:
                try:
                    pass
                except Exception:
                    pass
                user = None
            # DRF Token (no sobrescribir si ya autenticó con Clerk)
            if DRFToken is not None and user is None:
                try:
                    token_obj = DRFToken.objects.select_related('user').get(key=token_key)
                    user = token_obj.user
                except Exception:
                    # No cambiar user si falla este fallback
                    pass

            # Simple JWT
            if user is None and JWTAuthentication is not None:
                try:
                    jwt_auth = JWTAuthentication()
                    validated_token = jwt_auth.get_validated_token(token_key)
                    user = jwt_auth.get_user(validated_token)
                except Exception:
                    user = None

            if user is not None:
                # Asignar explícitamente el usuario obtenido al scope (no confiar sólo en el wrapper lazy)
                try:
                    self.scope['user'] = user
                except Exception:
                    # fallback: asignar como objeto simple
                    self.scope['user'] = user
            else:
                # leave as AnonymousUser; AuthMiddlewareStack may still set user from session
                self.scope['user'] = self.scope.get('user', AnonymousUser())

        # Debug/logging: mostrar subprotocols y resultado de autenticación (remover en producción)
        # Logs de diagnóstico: mostrar auth_result, variable local 'user' y scope['user']
        local_user = user if ('user' in locals()) else None
        try:

            try:
                pass
            except Exception:
                pass
            try:
                u = self.scope.get('user')
                pass
            except Exception:
                pass
        except Exception:
            pass

        # Si se envió token y no se autenticó, cerrar la conexión (si el cliente envió token inválido)
        # Preferir la variable local 'user' (resultado de la autenticación) para
        # decidir si el token fue validado. Esto evita falsos negativos si
        # `scope['user']` es un UserLazyObject que no refleja inmediatamente el valor.
        # Decidir cierre basándonos exclusivamente en la variable local 'user'
        current_user = user if ('user' in locals() and user is not None) else None
        if token_key and (current_user is None or isinstance(current_user, AnonymousUser)):
            try:
                ("WebSocket auth failed for token, closing connection")
            except Exception:
                pass
            self.close()
            return

        self.group_type = self.scope.get('url_route', {}).get('kwargs', {}).get('group_type')
        quote_id = self.scope.get('url_route', {}).get('kwargs', {}).get('quote_id')
        delivery_id = self.scope.get('url_route', {}).get('kwargs', {}).get('delivery_id')
        person_id = self.scope.get('url_route', {}).get('kwargs', {}).get('person_id')
        user_id = self.scope.get('url_route', {}).get('kwargs', {}).get('user_id')
        auth_user = self.scope.get('user')
        auth_user_id = getattr(auth_user, 'pk', None) or getattr(auth_user, 'userid', None)

        if self.group_type == 'quote' and quote_id:
            self.group_name = f"quote_{quote_id}"
        elif self.group_type == 'delivery' and delivery_id:
            self.group_name = f"delivery_{delivery_id}"
        elif self.group_type == 'new_quotes':
            self.group_name = "new_quotes"
        elif self.group_type == 'person_stats' and person_id:
            self.group_name = f"person_stats_{person_id}"
            self.person_id = person_id
        elif self.group_type == 'user_quotes' and user_id:
            if not self._owns_resource(auth_user_id, user_id):
                self.close()
                return
            self.user_id = str(user_id)
            self.group_name = f"user_quotes_{self.user_id}"
        elif self.group_type == 'user_deliveries' and user_id:
            if not self._owns_resource(auth_user_id, user_id):
                self.close()
                return
            self.user_id = str(user_id)
            self.group_name = f"user_deliveries_{self.user_id}"
        else:
            self.close()
            return

        async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
        # Para que el navegador complete el handshake correctamente, si el cliente
        # envió subprotocols debemos devolver uno en la respuesta. Si hay un
        # subprotocol coincidente (p. ej. el token enviado), usarlo; si no,
        # dejar que Channels acepte sin subprotocol.
        try:
            if matched_subprotocol:
                self.accept(subprotocol=matched_subprotocol)
            else:
                self.accept()
        except TypeError:
            # Compatibilidad: algunos entornos de channels usan 'subprotocols' arg
            try:
                if matched_subprotocol:
                    self.accept(subprotocols=[matched_subprotocol])
                else:
                    self.accept()
            except Exception:
                # Fallback: aceptar sin subprotocol
                self.accept()

        # Enviar quotes existentes (por ejemplo, status pending) al cliente que conecta
        if self.group_type == 'new_quotes':
            # Domiciliarios viendo lista de quotes - NO mostrar offers de otros domiciliarios
            try:
                qs = DeliveryQuote.objects.filter(status="pending")
                initial_quotes = DeliveryQuoteSerializer(qs, many=True).data
                
                # NO agregar offers aquí - vulnerabilidad de seguridad
                
                # Asegurar que los tipos no serializables por JSON (Decimal, UUID) se conviertan a str
                safe_initial = json.loads(json.dumps(initial_quotes, default=str))
                try:
                    self.send_json({"type": "initial_quotes", "quotes": safe_initial})
                except Exception:
                    # Evitar que una desconexión del cliente (ClientDisconnected)
                    # genere una excepción no manejada aquí. Importar localmente
                    # para no introducir dependencia si channels cambia.
                    try:
                        from channels.exceptions import ClientDisconnected
                    except Exception:
                        ClientDisconnected = None

                    if ClientDisconnected is not None:
                        try:
                            # Reintentar captura específica
                            self.send_json({"type": "initial_quotes", "quotes": safe_initial})
                        except Exception as exc_inner:
                            # Si el cliente ya se desconectó, ignorar silenciosamente
                            if isinstance(exc_inner, ClientDisconnected):
                                return
                            try:
                                pass
                            except Exception:
                                pass
                    else:
                        # Si no podemos identificar ClientDisconnected, loguear el error
                        try:
                            pass
                        except Exception:
                            pass
            except Exception as e:
                try:
                    pass
                except Exception:
                    pass
        
        elif self.group_type == 'quote':
            # Cliente viendo su cotización específica - SÍ mostrar todas las offers
            try:
                # Obtener solo el quote específico que está viendo
                qs = DeliveryQuote.objects.filter(id=quote_id, status="pending")
                initial_quotes = DeliveryQuoteSerializer(qs, many=True).data
                
                # Para este quote específico, agregar sus offers (el cliente debe verlas todas)
                for quote_data in initial_quotes:
                    quote_id_data = quote_data.get('id')
                    if quote_id_data:
                        offers = DeliveryOffer.objects.filter(quote_id=quote_id_data, status='pending')
                        quote_data['offers'] = DeliveryOfferSerializer(offers, many=True, context={'request': self.scope}).data
                
                # Asegurar que los tipos no serializables por JSON (Decimal, UUID) se conviertan a str
                safe_initial = json.loads(json.dumps(initial_quotes, default=str))
                try:
                    self.send_json({"type": "initial_quotes", "quotes": safe_initial})
                except Exception:
                    try:
                        from channels.exceptions import ClientDisconnected
                    except Exception:
                        ClientDisconnected = None

                    if ClientDisconnected is not None:
                        try:
                            self.send_json({"type": "initial_quotes", "quotes": safe_initial})
                        except Exception as exc_inner:
                            if isinstance(exc_inner, ClientDisconnected):
                                return
                            try:
                                pass
                            except Exception:
                                pass
                    else:
                        try:
                            pass
                        except Exception:
                            pass
            except Exception as e:
                try:
                    pass
                except Exception:
                    pass
        
        # Enviar estadísticas de domicilios completados para person_stats
        elif self.group_type == 'person_stats':
            try:
                from .models import Delivery
                from .serializers import DeliverySerializer
                from decimal import Decimal
                
                # Obtener domicilios completados (delivered o paid)
                deliveries = Delivery.objects.filter(
                    delivery_person_id=self.person_id,
                    status__in=['delivered', 'paid']
                )
                
                # Serializar los domicilios
                deliveries_data = DeliverySerializer(deliveries, many=True).data
                
                # Calcular el total
                total = sum(Decimal(str(d.final_price)) for d in deliveries)
                
                # Preparar respuesta
                response_data = {
                    'type': 'person_stats',
                    'deliveries': deliveries_data,
                    'total': str(total),
                    'count': deliveries.count()
                }
                
                # Convertir a tipos seguros para serialización
                safe_data = json.loads(json.dumps(response_data, default=str))
                
                self.send_json(safe_data)
            except Exception as e:
                try:
                    pass
                except Exception:
                    pass
        elif self.group_type == 'user_quotes':
            try:
                qs = DeliveryQuote.objects.filter(client_id=self.user_id).order_by('-created_at')
                initial_quotes = DeliveryQuoteSerializer(qs, many=True).data
                for quote_data in initial_quotes:
                    quote_id_data = quote_data.get('id')
                    if quote_id_data:
                        offers = DeliveryOffer.objects.filter(quote_id=quote_id_data)
                        quote_data['offers'] = DeliveryOfferSerializer(offers, many=True).data
                safe_initial = json.loads(json.dumps(initial_quotes, default=str))
                self.send_json({"type": "user_quotes.initial", "quotes": safe_initial})
            except Exception:
                try:
                    pass
                except Exception:
                    pass
        elif self.group_type == 'user_deliveries':
            try:
                deliveries = Delivery.objects.filter(client_id=self.user_id, status__in=IN_PROGRESS_STATUSES)
                deliveries_data = DeliverySerializer(deliveries, many=True).data
                safe_initial = json.loads(json.dumps(deliveries_data, default=str))
                self.send_json({"type": "user_deliveries.initial", "deliveries": safe_initial})
            except Exception:
                try:
                    pass
                except Exception:
                    pass

    def disconnect(self, close_code):
        if hasattr(self, 'group_name'):
            async_to_sync(self.channel_layer.group_discard)(self.group_name, self.channel_name)

    def receive_json(self, content, **kwargs):
        pass

    def broadcast(self, event):
        data = event.get('data', {})
        self.send_json(data)

    def _owns_resource(self, auth_user_id, requested_id):
        if not auth_user_id or not requested_id:
            return False
        return str(auth_user_id) == str(requested_id)