import jwt
import requests
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.core.cache import cache


class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token = auth_header.split(' ')[1]
        except IndexError:
            raise AuthenticationFailed('Formato de encabezado de autorización inválido.')

        try:
            jwks_data = cache.get('clerk_jwks')
            jwks_url = f"{settings.CLERK_FRONTEND_API_URL.rstrip('/')}/.well-known/jwks.json"
            response = requests.get(jwks_url)
            response.raise_for_status()
            jwks_data = response.json()
                

            public_keys = {}
            for jwk in jwks_data['keys']:
                kid = jwk['kid']
                public_keys[kid] = jwt.algorithms.RSAAlgorithm.from_jwk(jwk)

            unverified_header = jwt.get_unverified_header(token)
            kid = unverified_header['kid']
            public_key = public_keys.get(kid)

            if not public_key:
                raise AuthenticationFailed('Clave pública no encontrada.')

            # Asegúrate de que estos valores coincidan exactamente con tu configuración de Clerk
            expected_issuer = settings.CLERK_JWT_ISSUER
            expected_audience = settings.CLERK_JWT_AUDIENCE

            decoded_token = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=expected_audience,
                issuer=expected_issuer,
                options={"verify_signature": True},
                leeway=300
            )

            user_id = decoded_token.get('sub')
            if not user_id:
                raise AuthenticationFailed('Token inválido: falta el ID de usuario.')

            # Extraer datos adicionales del token (si están configurados en Clerk)
            first_name = decoded_token.get('first_name', '')
            last_name = decoded_token.get('last_name', '')
            username = decoded_token.get('username', '')
            image_url = decoded_token.get('image_url', '')
            email = decoded_token.get('email', '')

            from .models import User
            # Buscar o crear usuario
            try:
                user = User.objects.get(userid=user_id)
                
                # Fallback: Actualizar si los datos del token son más recientes/diferentes
                # Esto es útil si el webhook falló o aún no ha llegado
                needs_save = False
                if first_name and user.first_name != first_name:
                    user.first_name = first_name
                    needs_save = True
                if last_name and user.last_name != last_name:
                    user.last_name = last_name
                    needs_save = True
                if username and user.username != username:
                    user.username = username
                    needs_save = True
                if image_url and user.image_url != image_url:
                    user.image_url = image_url
                    needs_save = True
                if email and user.email != email:
                    user.email = email
                    needs_save = True
                
                if needs_save:
                    user.save()

            except User.DoesNotExist:
                # Crear usuario con todos los datos disponibles
                user = User.objects.create(
                    userid=user_id,
                    first_name=first_name,
                    last_name=last_name,
                    username=username,
                    image_url=image_url,
                    email=email
                )
            
            return (user, token)

        except requests.exceptions.RequestException as e:
            raise AuthenticationFailed('Error de red al obtener claves de autenticación.')
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token expirado.')
        except jwt.InvalidAudienceError:
            raise AuthenticationFailed('Audiencia de token inválida.')
        except jwt.InvalidIssuerError:
            raise AuthenticationFailed('Emisor de token inválido.')
        except jwt.InvalidTokenError as e:
            raise AuthenticationFailed(f'Token inválido: {e}')
        except Exception as e:
            raise AuthenticationFailed(f'Error de autenticación inesperado: {e}')

    def authenticate_header(self, request):
        return 'Bearer'