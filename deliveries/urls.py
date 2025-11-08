from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .api import (
    DeliveryQuoteViewSet, DeliveryOfferViewSet, DeliveryCategoryViewSet,
    DeliveryViewSet, DeliveryHistoryViewSet
)

router = DefaultRouter()
router.register(r'quotes', DeliveryQuoteViewSet, basename='delivery-quote')
router.register(r'offers', DeliveryOfferViewSet, basename='delivery-offer')
router.register(r'categories', DeliveryCategoryViewSet, basename='delivery-category')
router.register(r'deliveries', DeliveryViewSet, basename='delivery')
router.register(r'delivery-history', DeliveryHistoryViewSet, basename='delivery-history')

urlpatterns = [
    path('api/', include(router.urls)),
]