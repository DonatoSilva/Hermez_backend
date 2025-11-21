from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeliveryQuote, DeliveryOffer, DeliveryCategory, Delivery, DeliveryHistory
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliveryCategorySerializer, DeliverySerializer, DeliveryHistorySerializer
from deliveries.services.expiration import expire_quote_by_id

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
            status='assigned'
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

    @action(detail=True, methods=['post'], url_path='extend-expiration')
    def extend_expiration(self, request, pk=None):
        """Permite extender el tiempo de vida de una oferta pendiente."""
        offer = self.get_object()

        if offer.status != 'pending':
            return Response({'error': 'Solo se pueden extender ofertas pendientes'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            minutes = int(request.data.get('minutes') or request.data.get('extra_minutes'))
        except (TypeError, ValueError):
            return Response({'error': 'Debe proporcionar "minutes" como entero positivo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            offer.extend_expiration(minutes)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(offer)
        return Response({'status': 'extendido', 'expires_at': serializer.data['expires_at']})


class DeliveryQuoteViewSet(viewsets.ModelViewSet):
    queryset = DeliveryQuote.objects.all()
    serializer_class = DeliveryQuoteSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'], url_path='offers')
    def offers(self, request, pk=None):
        """Lista las ofertas asociadas a esta cotización.

        Permite filtrar por ?status=pending|accepted|rejected
        """
        quote = self.get_object()
        qs = quote.offers.all()
        status_filter = request.query_params.get('status')
        if status_filter:
            qs = qs.filter(status=status_filter)
        serializer = DeliveryOfferSerializer(qs, many=True)
        return Response(serializer.data)

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

    @action(detail=True, methods=['post'], url_path='extend-expiration')
    def extend_expiration(self, request, pk=None):
        """Extiende el tiempo de vida de una cotización pendiente"""
        quote = self.get_object()

        if quote.status != 'pending':
            return Response({'error': 'Solo se pueden extender cotizaciones pendientes'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            minutes = int(request.data.get('minutes') or request.data.get('extra_minutes'))
        except (TypeError, ValueError):
            return Response({'error': 'Debe proporcionar "minutes" como entero positivo'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quote.extend_expiration(minutes)
        except ValueError as exc:
            return Response({'error': str(exc)}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(quote)
        return Response({'status': 'extendido', 'expires_at': serializer.data['expires_at']})

    @action(detail=True, methods=['post'], url_path='expire-now')
    def expire_now(self, request, pk=None):
        """Forzar expiración inmediata de una cotización 'pending'.

        Permisos: dueño de la cotización (client) o staff.
        """
        quote = self.get_object()
        user = request.user

        if not (user.is_staff or user == quote.client):
            return Response({'error': 'No autorizado'}, status=status.HTTP_403_FORBIDDEN)

        if quote.status != 'pending':
            return Response({'error': 'Solo se pueden expirar cotizaciones en estado pendiente'},
                            status=status.HTTP_400_BAD_REQUEST)

        ok = expire_quote_by_id(quote.id)
        if not ok:
            return Response({'error': 'No fue posible expirar la cotización'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'expired', 'quote_id': str(quote.id)})


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