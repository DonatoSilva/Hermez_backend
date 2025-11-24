from django.test import TestCase

from users.models import User


class UserModelTest(TestCase):
    def test_toggle_availability(self):
        # Crear usuario con userid explícito (clave primaria)
        user = User.objects.create(userid='test_user_toggle')

        # Por defecto debe ser False
        self.assertFalse(user.is_available)

        # Llamar al método y verificar retorno y persistencia
        new_state = user.toggle_availability()
        user.refresh_from_db()
        self.assertTrue(new_state)
        self.assertTrue(user.is_available)

        # Llamar de nuevo para volver a False
        new_state2 = user.toggle_availability()
        user.refresh_from_db()
        self.assertFalse(new_state2)
        self.assertFalse(user.is_available)
