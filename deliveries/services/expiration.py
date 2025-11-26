from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from django.utils import timezone

from deliveries.models import DeliveryOffer, DeliveryQuote
from deliveries.serializers import DeliveryOfferSerializer, DeliveryQuoteSerializer


def _broadcast(group_name, payload):
    channel_layer = get_channel_layer()
    if not channel_layer or not group_name:
        return


    import json
    try:
        safe_payload = json.loads(json.dumps(payload, default=str))
    except Exception:
        try:
            safe_payload = str(payload)
        except Exception:
            safe_payload = {}

    async_to_sync(channel_layer.group_send)(group_name, {'type': 'broadcast', 'data': safe_payload})


def expire_quotes_and_offers():
    """Elimina cotizaciones y ofertas pendientes que hayan superado su fecha de expiración."""
    expired_quotes = _collect_expired_quotes()
    expired_offers = _collect_expired_offers()
    return expired_quotes, expired_offers

def _collect_expired_quotes():
    now = timezone.now()
    queryset = DeliveryQuote.objects.filter(status__in=['pending', 'cancelled'], expires_at__isnull=False, expires_at__lte=now)

    payloads = []
    for quote in queryset:
        payloads.append((quote.id, quote.client_id, DeliveryQuoteSerializer(quote).data))

    count = queryset.count()
    if count:
        queryset.delete()
        for quote_id, client_id, payload in payloads:
            event = {'type': 'quote_expired', 'data': payload}
            _broadcast('new_quotes', event)
            _broadcast(f'quote_{quote_id}', event)
            _broadcast(f'user_quotes_{client_id}', event)
    return count


def _collect_expired_offers():
    now = timezone.now()
    queryset = DeliveryOffer.objects.filter(status='pending', expires_at__isnull=False, expires_at__lte=now)

    payloads = []
    for offer in queryset.select_related('quote'):
        payloads.append((offer.quote_id, offer.quote.client_id, DeliveryOfferSerializer(offer).data))

    count = queryset.count()
    if count:
        queryset.delete()
        for quote_id, client_id, payload in payloads:
            event = {'type': 'offer_expired', 'data': payload}
            _broadcast(f'quote_{quote_id}', event)
            _broadcast(f'user_quotes_{client_id}', event)
    return count
