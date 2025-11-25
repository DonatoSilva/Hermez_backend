from django.urls import path
from .consumers import DeliveryConsumer

websocket_urlpatterns = [
    path('ws/deliveries/quotes/<uuid:quote_id>/', DeliveryConsumer.as_asgi(), {'group_type': 'quote'}),
    path('ws/deliveries/new-quotes/', DeliveryConsumer.as_asgi(), {'group_type': 'new_quotes'}),
    path('ws/deliveries/<uuid:delivery_id>/', DeliveryConsumer.as_asgi(), {'group_type': 'delivery'}),
    path('ws/deliveries/person/<str:person_id>/stats/', DeliveryConsumer.as_asgi(), {'group_type': 'person_stats'}),
    path('ws/deliveries/users/<str:user_id>/quotes/', DeliveryConsumer.as_asgi(), {'group_type': 'user_quotes'}),
    path('ws/deliveries/users/<str:user_id>/deliveries/', DeliveryConsumer.as_asgi(), {'group_type': 'user_deliveries'}),
]