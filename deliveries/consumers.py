from channels.generic.websocket import JsonWebsocketConsumer
from asgiref.sync import async_to_sync
from django.contrib.auth.models import AnonymousUser
from .models import DeliveryQuote
from .serializers import DeliveryQuoteSerializer

# Authentication helpers: try to support DRF Token and SimpleJWT if available
try:
    from rest_framework.authtoken.models import Token as DRFToken
except Exception:
    DRFToken = None

try:
    from rest_framework_simplejwt.authentication import JWTAuthentication
except Exception:
    JWTAuthentication = None

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
                        print("ClerkAuthentication auth_result:", repr(auth_result))
                    except Exception:
                        pass
                    if auth_result:
                        user = auth_result[0]
                except Exception as exc:
                    try:
                        print("ClerkAuthentication error:", repr(exc))
                    except Exception:
                        pass
                    user = None
            except Exception:
                try:
                    print("Failed to import ClerkAuthentication:")
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
            print("WS subprotocols:", subprotocols)
            print("Resolved token:", token_key)
            try:
                print("Local authenticated user (variable 'user'):", repr(local_user))
            except Exception:
                pass
            try:
                u = self.scope.get('user')
                print("Scope user object:", repr(u))
                print("Scope user.userid:", getattr(u, 'userid', None))
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
                print("WebSocket auth failed for token, closing connection")
            except Exception:
                pass
            self.close()
            return

        self.group_type = self.scope.get('url_route', {}).get('kwargs', {}).get('group_type')
        quote_id = self.scope.get('url_route', {}).get('kwargs', {}).get('quote_id')
        delivery_id = self.scope.get('url_route', {}).get('kwargs', {}).get('delivery_id')

        if self.group_type == 'quote' and quote_id:
            self.group_name = f"quote_{quote_id}"
        elif self.group_type == 'delivery' and delivery_id:
            self.group_name = f"delivery_{delivery_id}"
        elif self.group_type == 'new_quotes':
            self.group_name = "new_quotes"
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
        try:
            qs = DeliveryQuote.objects.filter(status="pending")
            initial = DeliveryQuoteSerializer(qs, many=True).data
            # Asegurar que los tipos no serializables por JSON (Decimal, UUID) se conviertan a str
            import json
            safe_initial = json.loads(json.dumps(initial, default=str))
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
                            print("Error al enviar initial_quotes:", repr(exc_inner))
                        except Exception:
                            pass
                else:
                    # Si no podemos identificar ClientDisconnected, loguear el error
                    try:
                        print("Error enviando quotes iniciales: cliente desconectado o envío falló")
                    except Exception:
                        pass
        except Exception as e:
            try:
                print("Error preparando/enviando quotes iniciales:", repr(e))
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