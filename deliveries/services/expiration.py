from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from deliveries.models import DeliveryOffer, DeliveryQuote
from deliveries.serializers import DeliveryOfferSerializer, DeliveryQuoteSerializer


def _broadcast(group_name, payload):
    channel_layer = get_channel_layer()
    if not channel_layer or not group_name:
        return
    async_to_sync(channel_layer.group_send)(group_name, {'type': 'broadcast', 'data': payload})


def expire_quotes_and_offers():
    """Elimina cotizaciones y ofertas pendientes que hayan superado su fecha de expiración."""
    expired_quotes = _collect_expired_quotes()
    expired_offers = _collect_expired_offers()
    return expired_quotes, expired_offers


def expire_quote_by_id(quote_id):
    """Expira de inmediato una cotización 'pending' por su ID.

    - Borra la cotización y sus ofertas relacionadas (cascade)
    - Emite broadcasts consistentes con la expiración regular
    - Retorna True si se expiró; False si no aplica (no existe o no está 'pending')
    """
    try:
        quote = DeliveryQuote.objects.get(id=quote_id, status='pending')
    except DeliveryQuote.DoesNotExist:
        return False

    payload = DeliveryQuoteSerializer(quote).data
    quote_id_str = str(quote.id)

    # Borrado en cascada (ofertas relacionadas)
    quote.delete()

    # Enviar los mismos eventos que la expiración programada
    _broadcast('new_quotes', {'type': 'quote.expired', 'data': payload})
    _broadcast(f'quote_{quote_id_str}', {'type': 'quote.expired', 'data': payload})
    return True


def _collect_expired_quotes():
    now = timezone.now()
    queryset = DeliveryQuote.objects.filter(status='pending', expires_at__isnull=False, expires_at__lte=now)

    payloads = []
    for quote in queryset:
        payloads.append((quote.id, DeliveryQuoteSerializer(quote).data))

    count = queryset.count()
    if count:
        queryset.delete()
        for quote_id, payload in payloads:
            _broadcast('new_quotes', {'type': 'quote.expired', 'data': payload})
            _broadcast(f'quote_{quote_id}', {'type': 'quote.expired', 'data': payload})
    return count


def _collect_expired_offers():
    now = timezone.now()
    queryset = DeliveryOffer.objects.filter(status='pending', expires_at__isnull=False, expires_at__lte=now)

    payloads = []
    for offer in queryset.select_related('quote'):
        payloads.append((offer.quote_id, DeliveryOfferSerializer(offer).data))

    count = queryset.count()
    if count:
        queryset.delete()
        for quote_id, payload in payloads:
            _broadcast(f'quote_{quote_id}', {'type': 'offer_expired', 'data': payload})
    return count
