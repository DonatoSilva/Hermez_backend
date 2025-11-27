from datetime import timedelta
from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid
from users.models import User

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
        ('cancelled', 'Cancelada'),
    ]
    PAYMENT_METHOD_CHOICES = [
        ('efectivo', 'Efectivo'),
        ('nequi', 'Nequi'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_quotes')
    pickup_address = models.TextField(null=False, blank=False)
    delivery_address = models.TextField(null=False, blank=False)
    category = models.ForeignKey(DeliveryCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    observations = models.JSONField(default=list, blank=True)
    vehicle_type = models.ForeignKey('vehicles.VehicleType', on_delete=models.SET_NULL, null=True, blank=True)
    estimated_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_size = models.CharField(max_length=100, blank=True, null=True)
    client_price = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, default='efectivo')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    history_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # ID único para todo el ciclo de vida

    class Meta:
        verbose_name = "Cotización de Entrega"
        verbose_name_plural = "Cotizaciones de Entrega"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"Cotización {self.id} - {self.client}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            ttl_minutes = getattr(settings, 'DELIVERIES_QUOTE_TTL_MINUTES', 10)
            self.expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        super().save(*args, **kwargs)

    def extend_expiration(self, minutes):
        if minutes <= 0:
            raise ValueError("Los minutos adicionales deben ser mayores a cero")
        base = self.expires_at or timezone.now()
        self.expires_at = base + timedelta(minutes=minutes)
        self.save(update_fields=['expires_at'])

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()


class DeliveryOffer(models.Model):
    """
    Modelo para ofertas de domiciliarios con gestión de ciclo de vida
    """
    STATUS_CHOICES = [
        ('pending', 'Pendiente'),
        ('accepted', 'Aceptada'),
        ('rejected', 'Rechazada'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_offers')
    quote = models.ForeignKey(DeliveryQuote, on_delete=models.CASCADE, related_name='offers')
    proposed_price = models.DecimalField(max_digits=10, decimal_places=2)
    estimated_delivery_time = models.DurationField(null=True, blank=True)
    vehicle = models.ForeignKey('vehicles.Vehicle', on_delete=models.SET_NULL, null=True, blank=True, related_name='delivery_offers')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True, db_index=True)

    class Meta:
        verbose_name = "Oferta de Domiciliario"
        verbose_name_plural = "Ofertas de Domiciliario"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
        ]
        unique_together = ['delivery_person', 'quote']  # Un domiciliario solo una oferta por cotización

    def __str__(self):
        return f"Oferta {self.id} - {self.delivery_person}"

    def save(self, *args, **kwargs):
        if not self.expires_at:
            ttl_minutes = getattr(settings, 'DELIVERIES_OFFER_TTL_MINUTES', 4)
            self.expires_at = timezone.now() + timedelta(minutes=ttl_minutes)
        super().save(*args, **kwargs)

    def extend_expiration(self, minutes):
        if minutes <= 0:
            raise ValueError("Los minutos adicionales deben ser mayores a cero")
        base = self.expires_at or timezone.now()
        self.expires_at = base + timedelta(minutes=minutes)
        self.save(update_fields=['expires_at'])

    @property
    def is_expired(self):
        return self.expires_at is not None and self.expires_at <= timezone.now()


class Delivery(models.Model):
    """
    Modelo para domicilios permanentes que se crean cuando una oferta es aceptada
    """
    STATUS_CHOICES = [
        ('assigned', 'Asignado'),
        ('picked_up', 'Recogido'),
        ('in_transit', 'En tránsito'),
        ('delivered', 'Entregado'),
        ('paid', 'Pagado'),
        ('cancelled', 'Cancelado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    client = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deliveries')
    delivery_person = models.ForeignKey(User, on_delete=models.CASCADE, related_name='assigned_deliveries', null=True, blank=True)
    pickup_address = models.TextField()
    delivery_address = models.TextField()
    category = models.ForeignKey(DeliveryCategory, on_delete=models.CASCADE)
    description = models.TextField(blank=True, null=True)
    observations = models.JSONField(default=list, blank=True)
    estimated_weight = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    estimated_size = models.CharField(max_length=100, blank=True, null=True)
    final_price = models.DecimalField(max_digits=10, decimal_places=2)
    vehicle = models.ForeignKey(
        'vehicles.Vehicle', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True,
        related_name='deliveries'
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='assigned')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)
    history_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)  # ID único para todo el ciclo de vida

    class Meta:
        verbose_name = "Domicilio"
        verbose_name_plural = "Domicilios"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['client']),
            models.Index(fields=['delivery_person']),
        ]

    def __str__(self):
        return f"Domicilio {self.id} - {self.client}"

    def save(self, *args, **kwargs):
        # Actualizar timestamps de finalización/cancelación según el estado
        if self.status == 'delivered' and not self.completed_at:
            self.completed_at = timezone.now()
        elif self.status == 'cancelled' and not self.cancelled_at:
            self.cancelled_at = timezone.now()
        super().save(*args, **kwargs)


class DeliveryHistory(models.Model):
    """
    Modelo para registrar el historial completo de eventos de un domicilio
    Incluye desde la creación de la cotización hasta la finalización del domicilio
    """
    EVENT_TYPE_CHOICES = [
        ('quote_created', 'Cotización Creada'),
        ('offer_made', 'Oferta Realizada'),
        ('offer_accepted', 'Oferta Aceptada'),
        ('status_changed', 'Estado Cambiado'),
        ('cancelled', 'Cancelado'),
        ('completed', 'Completado'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    history_id = models.UUIDField()  # ID único que conecta todo el ciclo de vida
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    description = models.TextField()
    changed_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='delivery_history_changes')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Historial de Domicilio"
        verbose_name_plural = "Historiales de Domicilio"
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['history_id']),
            models.Index(fields=['event_type']),
        ]

    def __str__(self):
        return f"Historial {self.id} - {self.get_event_type_display()}"
