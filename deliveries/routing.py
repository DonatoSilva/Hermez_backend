from django.urls import path
from .consumers import DeliveryConsumer

websocket_urlpatterns = [
    path('ws/deliveries/quotes/<uuid:quote_id>/', DeliveryConsumer.as_asgi(), {'group_type': 'quote'}),
    path('ws/deliveries/new-quotes/', DeliveryConsumer.as_asgi(), {'group_type': 'new_quotes'}),
    path('ws/deliveries/<uuid:delivery_id>/', DeliveryConsumer.as_asgi(), {'group_type': 'delivery'}),
]