from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeliveryQuote, DeliveryOffer, DeliveryCategory, Delivery, DeliveryHistory
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliveryCategorySerializer, DeliverySerializer, DeliveryHistorySerializer

class DeliveryCategoryViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCategory.objects.all()
    serializer_class = DeliveryCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def change_status(self, request, pk=None):
        """Cambiar el estado de un domicilio y registrar en el historial"""
        delivery = self.get_object()
        new_status = request.data.get('status')
        
        if not new_status:
            return Response({'error': 'Se requiere el nuevo estado'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_status not in dict(delivery.STATUS_CHOICES):
            return Response({'error': 'Estado inválido'}, status=status.HTTP_400_BAD_REQUEST)
        
        old_status = delivery.status
        delivery.status = new_status
        delivery.save()
        
        # Registrar en el historial
        DeliveryHistory.objects.create(
            history_id=delivery.history_id,
            event_type='status_changed',
            description=f'Estado cambiado de {old_status} a {new_status}',
            changed_by=request.user
        )
        
        return Response({'status': 'Estado actualizado correctamente'}, 
                        status=status.HTTP_200_OK)


class DeliveryOfferViewSet(viewsets.ModelViewSet):
    queryset = DeliveryOffer.objects.all()
    serializer_class = DeliveryOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def accept(self, request, pk=None):
        """Aceptar una oferta y crear el domicilio permanente"""
        offer = self.get_object()
        
        if offer.status != 'pending':
            return Response({'error': 'Solo se pueden aceptar ofertas pendientes'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Crear el domicilio permanente
        delivery = Delivery.objects.create(
            client=offer.quote.client,
            delivery_person=offer.delivery_person,
            pickup_address=offer.quote.pickup_address,
            delivery_address=offer.quote.delivery_address,
            category=offer.quote.category,
            description=offer.quote.description,
            estimated_weight=offer.quote.estimated_weight,
            estimated_size=offer.quote.estimated_size,
            final_price=offer.proposed_price,
            status='pending'
        )
        
        # Actualizar estados
        offer.status = 'accepted'
        offer.save()
        
        offer.quote.status = 'accepted'
        offer.quote.save()
        
        # Registrar eventos en el historial
        DeliveryHistory.objects.create(
            history_id=offer.quote.history_id,
            event_type='offer_accepted',
            description=f'Oferta aceptada por {offer.delivery_person} con precio ${offer.proposed_price}',
            changed_by=request.user
        )
        
        # Asignar el mismo history_id al delivery para mantener la continuidad
        delivery.history_id = offer.quote.history_id
        delivery.save()
        
        DeliveryHistory.objects.create(
            history_id=delivery.history_id,
            event_type='offer_accepted',
            description=f'Domicilio creado a partir de oferta aceptada',
            changed_by=request.user
        )
        
        # Eliminar objetos temporales (opcional - se puede hacer después)
        # offer.delete()
        # offer.quote.delete()
        
        return Response({
            'message': 'Oferta aceptada y domicilio creado',
            'delivery_id': str(delivery.id)
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'])
    def reject(self, request, pk=None):
        """Rechazar una oferta"""
        offer = self.get_object()
        
        if offer.status != 'pending':
            return Response({'error': 'Solo se pueden rechazar ofertas pendientes'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        offer.status = 'rejected'
        offer.save()
        
        # Registrar en el historial
        DeliveryHistory.objects.create(
            history_id=offer.quote.history_id,
            event_type='offer_made',
            description=f'Oferta rechazada por el cliente',
            changed_by=request.user
        )
        
        return Response({'status': 'Oferta rechazada'})


class DeliveryQuoteViewSet(viewsets.ModelViewSet):
    queryset = DeliveryQuote.objects.all()
    serializer_class = DeliveryQuoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar una cotización y eliminar objetos relacionados"""
        quote = self.get_object()
        
        if quote.status != 'pending':
            return Response({'error': 'Solo se pueden cancelar cotizaciones pendientes'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        # Registrar en el historial antes de eliminar
        DeliveryHistory.objects.create(
            history_id=quote.history_id,
            event_type='cancelled',
            description='Cotización cancelada por el cliente',
            changed_by=request.user
        )
        
        # Eliminar ofertas relacionadas
        quote.offers.all().delete()
        
        # Eliminar la cotización
        quote.delete()
        
        return Response({'status': 'Cotización cancelada y eliminada'})


class DeliveryHistoryViewSet(viewsets.ReadOnlyModelViewSet):
    """API para consultar el historial de eventos de domicilios usando history_id"""
    serializer_class = DeliveryHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        queryset = DeliveryHistory.objects.all()
        
        # Filtrar por history_id - el ID único que conecta todo el ciclo de vida
        history_id = self.request.query_params.get('history_id')
        if history_id:
            # Buscar eventos con este history_id
            queryset = queryset.filter(history_id=history_id)
            return queryset.order_by('created_at')
            
        return queryset.order_by('created_at')