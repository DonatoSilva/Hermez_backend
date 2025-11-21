from django.core.management.base import BaseCommand

from deliveries.services.expiration import expire_quotes_and_offers


class Command(BaseCommand):
    help = 'Elimina cotizaciones y ofertas expiradas'

    def handle(self, *args, **options):
        quotes_removed, offers_removed = expire_quotes_and_offers()
        self.stdout.write(
            self.style.SUCCESS(
                f'Cotizaciones eliminadas: {quotes_removed} | Ofertas eliminadas: {offers_removed}'
            )
        )
