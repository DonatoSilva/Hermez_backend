from django.urls import path
from .api import AddressViewSet

urlpatterns = [
    path('addresses/', AddressViewSet.as_view({'get': 'list', 'post': 'create'}), name='user-address-list'),
    path('addresses/<uuid:pk>/', AddressViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-address-detail'),
    path('addresses/<uuid:pk>/add-favorite/', AddressViewSet.as_view({'post': 'add_favorite'}), name='user-address-add-favorite'),
]
