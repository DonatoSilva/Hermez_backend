from django.db import models
from django.utils import timezone
import uuid
from users.models import User
from addresses.models import Address

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


class DeliveryQuote(models.Model):
    """
    Modelo para solicitudes de entrega de clientes con gestión de ciclo de vida
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('expired', 'Expirada'),
        ('cancelled', 'Cancelada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_quotes')
    pickup_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='pickup_quotes')
    delivery_address = models.ForeignKey(Address, on_delete=models.CASCADE, related_name='delivery_quotes')
    category = models.ForeignKey(DeliveryCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    estimated_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_size = models.CharField(max_length=100, blank=True, null=True)
    client_price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()  # Fecha de expiración automática
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Cotización de Entrega"
        verbose_name_plural = "Cotizaciones de Entrega"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"Cotización {self.id} - {self.client}"

    def save(self, *args, **kwargs):
        # Establecer expiración por defecto (48 horas) si no se especifica
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=48)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Verifica si la cotización ha expirado"""
        return timezone.now() > self.expires_at

    def deactivate(self):
        """Desactiva la cotización"""
        self.is_active = False
        self.status = 'expired'
        self.save()

    @classmethod
    def cleanup_expired(cls, days=30):
        """Método de clase para limpiar cotizaciones expiradas"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_quotes = cls.objects.filter(
            expires_at__lt=timezone.now(),
            status__in=['pending', 'expired'],
            is_active=True,
            updated_at__lt=cutoff_date
        )
        
        deactivated_count = expired_quotes.update(is_active=False, status='expired')
        return deactivated_count

    @classmethod
    def purge_old_inactive(cls, days=90):
        """Elimina permanentemente cotizaciones inactivas muy antiguas"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_quotes = cls.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        )
        
        deleted_count = old_quotes.count()
        old_quotes.delete()
        return deleted_count


class DeliveryOffer(models.Model):
    """
    Modelo para ofertas de domiciliarios con gestión de ciclo de vida
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
        ('expired', 'Expirada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_offers')
    quote = models.ForeignKey(DeliveryQuote, on_delete=models.CASCADE, related_name='offers')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_time = models.DurationField(null=True, blank=True)
    vehicle_type = models.ForeignKey('vehicles.VehicleType', on_delete=models.SET_NULL, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    expires_at = models.DateTimeField()  # Fecha de expiración automática
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Oferta de Domiciliario"
        verbose_name_plural = "Ofertas de Domiciliario"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'expires_at']),
            models.Index(fields=['is_active']),
        ]
        unique_together = ['delivery_person', 'quote']  # Un domiciliario solo una oferta por cotización

    def __str__(self):
        return f"Oferta {self.id} - {self.delivery_person}"

    def save(self, *args, **kwargs):
        # Establecer expiración por defecto (24 horas) si no se especifica
        if not self.expires_at:
            self.expires_at = timezone.now() + timezone.timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_expired(self):
        """Verifica si la oferta ha expirado"""
        return timezone.now() > self.expires_at

    def deactivate(self):
        """Desactiva la oferta"""
        self.is_active = False
        if self.status == 'pending':
            self.status = 'expired'
        self.save()

    @classmethod
    def cleanup_expired(cls, days=30):
        """Método de clase para limpiar ofertas expiradas"""
        from django.utils import timezone
        from datetime import timedelta
        from django.db import models
        
        cutoff_date = timezone.now() - timedelta(days=days)
        expired_offers = cls.objects.filter(
            models.Q(expires_at__lt=timezone.now()) |
            models.Q(status='rejected'),
            is_active=True,
            created_at__lt=cutoff_date
        )
        
        deactivated_count = expired_offers.update(is_active=False)
        return deactivated_count

    @classmethod
    def purge_old_inactive(cls, days=90):
        """Elimina permanentemente ofertas inactivas muy antiguas"""
        from django.utils import timezone
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days)
        old_offers = cls.objects.filter(
            is_active=False,
            updated_at__lt=cutoff_date
        )
        
        deleted_count = old_offers.count()
        old_offers.delete()
        return deleted_count