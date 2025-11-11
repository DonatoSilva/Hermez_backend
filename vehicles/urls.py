from django.urls import path
from .api import VehicleViewSet, VehicleTypeViewSet

urlpatterns = [
    path('vehicles/', VehicleViewSet.as_view({'get': 'list', 'post': 'create'}), name='vehicle-list'),
    path('vehicles/<uuid:pk>/', VehicleViewSet.as_view({'get': 'retrieve', 'put': 'update', 'patch': 'partial_update', 'delete': 'destroy'}), name='vehicle-detail'),
    path('vehicle-types/', VehicleTypeViewSet.as_view({'get': 'list'}), name='vehicletype-list'),
]