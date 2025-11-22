from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import DeliveryQuote, DeliveryOffer, Delivery
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliverySerializer

channel_layer = get_channel_layer()

@receiver(post_save, sender=DeliveryQuote)
def on_quote_created(sender, instance, created, **kwargs):
    if created:
        data = DeliveryQuoteSerializer(instance).data
        async_to_sync(channel_layer.group_send)(
            'new_quotes',
            {'type': 'broadcast', 'data': {'type': 'quote_created', 'data': data}}
        )
        async_to_sync(channel_layer.group_send)(
            f'quote_{instance.id}',
            {'type': 'broadcast', 'data': {'type': 'quote_created', 'data': data}}
        )

@receiver(post_save, sender=DeliveryOffer)
def on_offer_saved(sender, instance, created, **kwargs):
    data = DeliveryOfferSerializer(instance).data
    event_type = 'offer_made' if created else 'offer_updated'
    async_to_sync(channel_layer.group_send)(
        f'quote_{instance.quote.id}',
        {'type': 'broadcast', 'data': {'type': event_type, 'data': data}}
    )
    if instance.status == 'accepted':
        async_to_sync(channel_layer.group_send)(
            f'quote_{instance.quote.id}',
            {'type': 'broadcast', 'data': {'type': 'offer.accepted', 'data': data}}
        )

@receiver(post_save, sender=Delivery)
def on_delivery_saved(sender, instance, created, **kwargs):
    data = DeliverySerializer(instance).data
    event_type = 'delivery.created' if created else 'delivery.status'
    async_to_sync(channel_layer.group_send)(
        f'delivery_{instance.id}',
        {'type': 'broadcast', 'data': {'type': event_type, 'data': data}}
    )