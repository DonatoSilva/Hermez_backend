from django.urls import path
from .api import AddressViewSet

urlpatterns = [
    path('<uuid:user_id>/addresses/', AddressViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-address-list'),
    path('<uuid:user_id>/addresses/<uuid:pk>/', AddressViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-address-detail'),
]
