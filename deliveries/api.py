from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeliveryQuote, DeliveryOffer, DeliveryCategory
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliveryCategorySerializer


class DeliveryQuoteViewSet(viewsets.ModelViewSet):
    queryset = DeliveryQuote.objects.all()
    serializer_class = DeliveryQuoteSerializer


class DeliveryOfferViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOffer.objects.all()
    serializer_class = DeliveryOfferSerializer


class DeliveryCategoryViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCategory.objects.all()
    serializer_class = DeliveryCategorySerializer