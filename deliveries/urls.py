from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    DeliveryQuoteViewSet, DeliveryOfferViewSet, DeliveryCategoryViewSet,
    DeliveryViewSet
)

router = DefaultRouter()
router.register(r'quotes', DeliveryQuoteViewSet, basename='delivery-quote')
router.register(r'offers', DeliveryOfferViewSet, basename='delivery-offer')
router.register(r'categories', DeliveryCategoryViewSet, basename='delivery-category')
router.register(r'', DeliveryViewSet, basename='delivery')

urlpatterns = [
    path('api/', include(router.urls)),
]