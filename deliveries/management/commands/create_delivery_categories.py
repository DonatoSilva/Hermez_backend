from django.core.management.base import BaseCommand
from deliveries.models import DeliveryCategory

class Command(BaseCommand):
    help = 'Crea categorías de entrega iniciales en la base de datos'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'Comida', 'description': 'Entrega de alimentos y comidas preparadas.'},
            {'name': 'Paquetes', 'description': 'Entrega de paquetes y mercancías de tamaño pequeño a mediano.'},
            {'name': 'Documentos', 'description': 'Transporte seguro y rápido de documentos importantes.'},
            {'name': 'Personas', 'description': 'Transporte de pasajeros.'},
            {'name': 'Mercado', 'description': 'Entrega de compras de supermercado y abarrotes.'},
        ]

        for category_data in categories:
            category, created = DeliveryCategory.objects.get_or_create(
                name=category_data['name'],
                defaults={'description': category_data['description']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Categoría creada: "{category.name}"'))
            else:
                self.stdout.write(self.style.WARNING(f'La categoría "{category.name}" ya existe.'))