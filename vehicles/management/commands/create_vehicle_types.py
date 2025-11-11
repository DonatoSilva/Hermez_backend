from django.core.management.base import BaseCommand
from vehicles.models import VehicleType
from deliveries.models import DeliveryCategory

class Command(BaseCommand):
    help = 'Crea tipos de vehículo iniciales en la base de datos'

    def handle(self, *args, **kwargs):
        vehicle_types = [
            {
                'name': 'Moto',
                'description': 'Vehículo ágil para entregas rápidas en la ciudad.',
                'max_weight_capacity_kg': 150,
                'max_volume_capacity_liters': 80,
                'passenger_capacity': 1,
                'delivery_categories': ['Comida', 'Paquetes', 'Documentos', 'Personas', 'Mercado']
            },
            {
                'name': 'Carro',
                'description': 'Vehículo con mayor capacidad para entregas más grandes o múltiples.',
                'max_weight_capacity_kg': 500,
                'max_volume_capacity_liters': 1500,
                'passenger_capacity': 4,
                'delivery_categories': ['Paquetes', 'Personas', 'Mercado']
            },
            {
                'name': 'Motocarro',
                'description': 'Vehículo versátil con capacidad de carga media.',
                'max_weight_capacity_kg': 200,
                'max_volume_capacity_liters': 1000,
                'passenger_capacity': 3,
                'delivery_categories': ['Comida', 'Paquetes', 'Mercado', 'Personas']
            },
        ]

        for vehicle_data in vehicle_types:
            vehicle_type, created = VehicleType.objects.get_or_create(
                name=vehicle_data['name'],
                defaults={
                    'description': vehicle_data['description'],
                    'max_weight_capacity_kg': vehicle_data['max_weight_capacity_kg'],
                    'max_volume_capacity_liters': vehicle_data['max_volume_capacity_liters'],
                    'passenger_capacity': vehicle_data['passenger_capacity'],
                }
            )

            if created:
                self.stdout.write(self.style.SUCCESS(f'Tipo de vehículo creado: "{vehicle_type.name}"'))
            else:
                self.stdout.write(self.style.WARNING(f'El tipo de vehículo "{vehicle_type.name}" ya existe.'))

            categories = DeliveryCategory.objects.filter(name__in=vehicle_data['delivery_categories'])
            vehicle_type.delivery_categories.set(categories)