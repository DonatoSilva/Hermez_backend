from django.db import models
from django.utils.crypto import get_random_string
import uuid

class User(models.Model):
    userid = models.CharField(primary_key=True, editable=True, default=f"user_{get_random_string(12)}", blank=True, unique=True)
    gender = models.CharField(max_length=6, choices=[
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
    ], blank=True, null=True)
    phone = models.CharField(max_length=10, blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)

    # Campo de contraseña requerido por Django, pero no usado por Clerk
    password = models.CharField(max_length=128, blank=True, null=True)

    USERNAME_FIELD = 'userid'
    REQUIRED_FIELDS = []

    # Propiedades y métodos requeridos por el sistema de autenticación de Django
    @property
    def is_authenticated(self):
        return True # Siempre True si el token de Clerk es válido

    @property
    def is_active(self):
        return True # Asumimos que los usuarios de Clerk están activos

    @property
    def is_staff(self):
        return False # Los usuarios de Clerk no son staff por defecto

    @property
    def is_superuser(self):
        return False # Los usuarios de Clerk no son superusuarios por defecto

    def get_full_name(self):
        return self.userid # O cualquier otro campo que quieras usar como nombre completo

    def get_short_name(self):
        return self.userid # O cualquier otro campo que quieras usar como nombre corto

    @property
    def is_anonymous(self):
        return False # Los usuarios autenticados por Clerk no son anónimos

    def __str__(self):
        return f"User {self.userid}"

class UserRating(models.Model):
    userRatingId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings')
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings')
    rating = models.IntegerField()
    comment = models.TextField()
    
    class Meta:
        db_table = 'user_rating'

    def __str__(self):
        return f"Rating {self.userRatingId} - Score: {self.rating}"
