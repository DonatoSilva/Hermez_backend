from django.core.validators import MaxValueValidator, MinValueValidator
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
    role = models.CharField(max_length=10, choices=[
        ('client', 'Client'),
        ('delivery', 'Delivery'),
    ], blank=True, null=True)
    is_online = models.BooleanField(default=False)
    is_available = models.BooleanField(default=False)
    current_vehicle = models.ForeignKey(
        'vehicles.Vehicle', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='active_drivers'
    )

    # Campos sincronizados desde Clerk
    first_name = models.CharField(max_length=150, blank=True, null=True)
    last_name = models.CharField(max_length=150, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    username = models.CharField(max_length=150, blank=True, null=True, unique=True)
    image_url = models.URLField(max_length=500, blank=True, null=True)

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
        full_name = f"{self.first_name or ''} {self.last_name or ''}".strip()
        return full_name if full_name else self.userid

    def get_short_name(self):
        return self.first_name or self.userid

    @property
    def is_anonymous(self):
        return False # Los usuarios autenticados por Clerk no son anónimos

    def __str__(self):
        return f"User {self.userid}"

class UserRating(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    ratee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_ratings', editable=False)
    rater = models.ForeignKey(User, on_delete=models.CASCADE, related_name='given_ratings', editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(10)])
    comment = models.TextField(blank=True, null=True)
    
    class Meta:
        db_table = 'user_rating'

    def __str__(self):
        return f"Rating {self.id} - Score: {self.rating}"
