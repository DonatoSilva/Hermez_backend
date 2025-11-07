from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import VehicleViewSet

router = DefaultRouter()
router.register(r'vehicles', VehicleViewSet, basename='vehicle')

urlpatterns = [
    path('me/', include(router.urls)),
]