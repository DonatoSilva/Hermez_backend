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
                options={"verify_signature": True}
            )

            user_id = decoded_token.get('sub')
            if not user_id:
                raise AuthenticationFailed('Token inválido: falta el ID de usuario.')

            # Aquí puedes buscar o crear el usuario en tu base de datos
            # Por ahora, solo devolvemos un usuario ficticio o el ID de Clerk
            from .models import User # Asumiendo que tienes un modelo User
            try:
                user = User.objects.get(userid=user_id)
            except User.DoesNotExist:
                # Si el usuario no existe en tu DB, puedes crearlo o levantar un error
                user = User.objects.create(userid=user_id)
            
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