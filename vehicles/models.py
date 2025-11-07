from django.db import models
from users.models import User
import uuid


class VehicleType(models.Model):
    """
    Modelo para tipos de vehículos con capacidades y categorías específicas
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    max_weight_capacity_kg = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    max_volume_capacity_liters = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    passenger_capacity = models.IntegerField(blank=True, null=True)
    delivery_categories = models.ManyToManyField('deliveries.DeliveryCategory', blank=True)
    image = models.URLField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tipo de Vehículo"
        verbose_name_plural = "Tipos de Vehículos"
        ordering = ['name']

    def __str__(self):
        return self.name


class Vehicle(models.Model):
    vehicleId = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    userId = models.ForeignKey(User, on_delete=models.CASCADE, related_name='vehicles')
    type = models.ForeignKey(VehicleType, on_delete=models.PROTECT, null=True, blank=True, related_name='vehicles')
    brand = models.CharField(max_length=50)
    model = models.CharField(max_length=50)
    year = models.IntegerField()
    licensePlate = models.CharField(max_length=20, unique=True)
    vin = models.CharField(max_length=17, unique=True)
    color = models.CharField(max_length=30)
    driverLicenseStatus = models.CharField(max_length=20, default='pending')
    registrationCardStatus = models.CharField(max_length=20, default='pending')
    insurancePolicyStatus = models.CharField(max_length=20, default='pending')
    criminalRecordStatus = models.CharField(max_length=20, default='pending')
    isVerified = models.BooleanField(default=False)
    verificationNotes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f'{self.brand} {self.model} ({self.licensePlate})'
