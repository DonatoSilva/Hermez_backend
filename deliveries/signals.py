from django.db.models.signals import post_save
from django.dispatch import receiver
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from .models import DeliveryQuote, DeliveryOffer, Delivery
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliverySerializer
import json

channel_layer = get_channel_layer()

@receiver(post_save, sender=DeliveryQuote)
def on_quote_created(sender, instance, created, **kwargs):
    if created:
        data = DeliveryQuoteSerializer(instance).data
        # Convertir a JSON y back para asegurar que todos los tipos son serializables
        safe_data = json.loads(json.dumps(data, default=str))
        async_to_sync(channel_layer.group_send)(
            'new_quotes',
            {'type': 'broadcast', 'data': {'type': 'quote_created', 'data': safe_data}}
        )
        async_to_sync(channel_layer.group_send)(
            f'quote_{instance.id}',
            {'type': 'broadcast', 'data': {'type': 'quote_created', 'data': safe_data}}
        )

@receiver(post_save, sender=DeliveryOffer)
def on_offer_saved(sender, instance, created, **kwargs):
    data = DeliveryOfferSerializer(instance).data
    # Convertir a JSON y back para asegurar que todos los tipos son serializables
    safe_data = json.loads(json.dumps(data, default=str))
    event_type = 'offer_made' if created else 'offer_updated'
    async_to_sync(channel_layer.group_send)(
        f'quote_{instance.quote.id}',
        {'type': 'broadcast', 'data': {'type': event_type, 'data': safe_data}}
    )
    if instance.status == 'accepted':
        async_to_sync(channel_layer.group_send)(
            f'quote_{instance.quote.id}',
            {'type': 'broadcast', 'data': {'type': 'offer.accepted', 'data': safe_data}}
        )

@receiver(post_save, sender=Delivery)
def on_delivery_saved(sender, instance, created, **kwargs):
    data = DeliverySerializer(instance).data
    # Convertir a JSON y back para asegurar que todos los tipos son serializables
    safe_data = json.loads(json.dumps(data, default=str))
    event_type = 'delivery.created' if created else 'delivery.status'
    async_to_sync(channel_layer.group_send)(
        f'delivery_{instance.id}',
        {'type': 'broadcast', 'data': {'type': event_type, 'data': safe_data}}
    )