from django.db import models
import uuid

# Create your models here.


class DeliveryCategory(models.Model):
    """
    Modelo para categorizar los tipos de entregas que pueden realizar los vehículos
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Categoría de Entrega"
        verbose_name_plural = "Categorías de Entrega"
        ordering = ['name']

    def __str__(self):
        return self.name