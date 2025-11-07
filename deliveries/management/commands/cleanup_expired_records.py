from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from django.db import models
from deliveries.models import DeliveryQuote, DeliveryOffer

class Command(BaseCommand):
    help = 'Limpia registros expirados de DeliveryQuote y DeliveryOffer'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Número de días para considerar registros como expirados (por defecto: 30)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué registros se eliminarían sin realizar cambios'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        cutoff_date = timezone.now() - timedelta(days=days)

        self.stdout.write(
            self.style.NOTICE(
                f"Limpiando registros expirados anteriores a {cutoff_date.strftime('%Y-%m-%d %H:%M:%S')}"
            )
        )

        # Limpiar DeliveryQuote expiradas
        expired_quotes = DeliveryQuote.objects.filter(
            expires_at__lt=timezone.now(),
            status__in=['pending', 'expired'],
            is_active=True
        )

        self.stdout.write(f"Cotizaciones expiradas encontradas: {expired_quotes.count()}")

        if not dry_run:
            deactivated_quotes = expired_quotes.update(is_active=False)
            self.stdout.write(
                self.style.SUCCESS(f"Cotizaciones desactivadas: {deactivated_quotes}")
            )
        else:
            for quote in expired_quotes:
                self.stdout.write(
                    f"[DRY RUN] Se desactivaría: {quote} (expiró: {quote.expires_at})"
                )

        # Limpiar DeliveryOffer expiradas o rechazadas
        expired_offers = DeliveryOffer.objects.filter(
            models.Q(expires_at__lt=timezone.now()) |
            models.Q(status='rejected'),
            is_active=True,
            created_at__lt=cutoff_date
        )

        self.stdout.write(f"Ofertas expiradas/rechazadas encontradas: {expired_offers.count()}")

        if not dry_run:
            deactivated_offers = expired_offers.update(is_active=False)
            self.stdout.write(
                self.style.SUCCESS(f"Ofertas desactivadas: {deactivated_offers}")
            )
        else:
            for offer in expired_offers:
                self.stdout.write(
                    f"[DRY RUN] Se desactivaría: {offer} (estado: {offer.status}, expira: {offer.expires_at})"
                )

        # Limpieza definitiva de registros muy antiguos (más de 90 días)
        old_cutoff_date = timezone.now() - timedelta(days=90)
        old_inactive_quotes = DeliveryQuote.objects.filter(
            is_active=False,
            updated_at__lt=old_cutoff_date
        )
        old_inactive_offers = DeliveryOffer.objects.filter(
            is_active=False,
            updated_at__lt=old_cutoff_date
        )

        self.stdout.write(f"Cotizaciones inactivas antiguas: {old_inactive_quotes.count()}")
        self.stdout.write(f"Ofertas inactivas antiguas: {old_inactive_offers.count()}")

        if not dry_run:
            deleted_quotes = old_inactive_quotes.count()
            deleted_offers = old_inactive_offers.count()
            old_inactive_quotes.delete()
            old_inactive_offers.delete()
            
            self.stdout.write(
                self.style.WARNING(f"Cotizaciones eliminadas permanentemente: {deleted_quotes}")
            )
            self.stdout.write(
                self.style.WARNING(f"Ofertas eliminadas permanentemente: {deleted_offers}")
            )
        else:
            for quote in old_inactive_quotes:
                self.stdout.write(
                    f"[DRY RUN] Se eliminaría permanentemente: {quote} (última actualización: {quote.updated_at})"
                )
            for offer in old_inactive_offers:
                self.stdout.write(
                    f"[DRY RUN] Se eliminaría permanentemente: {offer} (última actualización: {offer.updated_at})"
                )

        if not dry_run:
            self.stdout.write(
                self.style.SUCCESS("Limpieza completada exitosamente")
            )
        else:
            self.stdout.write(
                self.style.NOTICE("Ejecución en modo dry-run - No se realizaron cambios")
            )