from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from django.contrib.auth import get_user_model
from django.conf import settings
import jwt
import requests
from django.core.cache import cache
from jwt.algorithms import RSAAlgorithm

User = get_user_model()

class ClerkAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.headers.get('Authorization')

        if not auth_header:
            return None

        try:
            token_type, token = auth_header.split(' ')
            if token_type.lower() != 'bearer':
                return None
        except ValueError:
            return None

        try:
            # Obtener JWKS de Clerk (cacheado para eficiencia)
            jwks_data = cache.get('clerk_jwks')
            if not jwks_data:
                jwks_url = f"https://{settings.CLERK_FRONTEND_API_URL}/.well-known/jwks.json"
                response = requests.get(jwks_url)
                response.raise_for_status()
                jwks_data = response.json()
                cache.set('clerk_jwks', jwks_data, timeout=3600)  # Cache por 1 hora

            # Encontrar la clave de firma correcta
            header = jwt.get_unverified_header(token)
            kid = header['kid']
            public_key = None
            for key in jwks_data['keys']:
                if key['kid'] == kid:
                    public_key = RSAAlgorithm.from_jwk(key)
                    break

            if not public_key:
                raise AuthenticationFailed('Clave de firma JWT no encontrada.')

            # Decodificar y verificar el token
            payload = jwt.decode(
                token,
                public_key,
                algorithms=["RS256"],  # Clerk usa RS256 por defecto
                audience=settings.CLERK_JWT_AUDIENCE,
                issuer=settings.CLERK_JWT_ISSUER,
                options={"verify_signature": True}
            )

            clerk_user_id = payload.get('sub')

            if not clerk_user_id:
                raise AuthenticationFailed('No se encontró el ID de usuario de Clerk en el token.')

            # Busca o crea el usuario en tu base de datos de Django
            # Asignamos el clerk_id como userid para mantener trazabilidad fácil
            user, created = User.objects.get_or_create(
                clerk_id=clerk_user_id, 
                defaults={
                    'userid': clerk_user_id,  # Usar el mismo ID de Clerk como userid
                    'gender': 'other',  # Valor por defecto, se puede actualizar después
                    'phone': '',  # Valor por defecto, se puede actualizar después
                    'age': 0  # Valor por defecto, se puede actualizar después
                }
            )

            return (user, token)
        except jwt.ExpiredSignatureError:
            raise AuthenticationFailed('Token de autenticación expirado.')
        except jwt.InvalidTokenError:
            raise AuthenticationFailed('Token de autenticación inválido.')
        except requests.exceptions.RequestException as e:
            raise AuthenticationFailed(f'Error al obtener JWKS de Clerk: {e}')
        except Exception as e:
            raise AuthenticationFailed(f'Error de autenticación: {e}')

    def authenticate_header(self, request):
        return 'Bearer'