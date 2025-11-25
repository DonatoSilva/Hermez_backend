from rest_framework import permissions, viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import DeliveryQuote, DeliveryOffer, DeliveryCategory, Delivery, DeliveryHistory
from deliveries.services.expiration import _broadcast
from .serializers import DeliveryQuoteSerializer, DeliveryOfferSerializer, DeliveryCategorySerializer, DeliverySerializer, DeliveryHistorySerializer

class DeliveryCategoryViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCategory.objects.all()
    serializer_class = DeliveryCategorySerializer
    permission_classes = [permissions.IsAuthenticated]

class DeliveryViewSet(viewsets.ModelViewSet):
    queryset = Delivery.objects.all()
    serializer_class = DeliverySerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['get'])
    def history(self, request, pk=None):
        """Obtener el domicilio con todo su historial de eventos"""
        delivery = self.get_object()
        
        # Obtener el historial usando el history_id
        history_events = DeliveryHistory.objects.filter(
            history_id=delivery.history_id
        ).order_by('created_at')
        
        # Serializar
        delivery_data = DeliverySerializer(delivery).data
        history_data = DeliveryHistorySerializer(history_events, many=True).data
        
        return Response({
            'delivery': delivery_data,
            'history': history_data
        })

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

        quote_payload = DeliveryQuoteSerializer(offer.quote, context={'request': request}).data
        delivery_payload = DeliverySerializer(delivery, context={'request': request}).data
        _broadcast(f'quote_{str(offer.quote.id)}', {'type': 'quote_updated', 'data': quote_payload})
        _broadcast(f'user_quotes_{offer.quote.client_id}', {'type': 'quote_updated', 'data': quote_payload})
        _broadcast(f'user_deliveries_{delivery.client_id}', {'type': 'delivery_created', 'data': delivery_payload})
        
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

        offer_payload = DeliveryOfferSerializer(offer, context={'request': request}).data
        _broadcast(f'quote_{str(offer.quote.id)}', {'type': 'offer_rejected', 'data': offer_payload})
        _broadcast(f'user_quotes_{offer.quote.client_id}', {'type': 'offer_rejected', 'data': offer_payload})

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

    def get_queryset(self):
        """Limit access so users only see their own quotes unless staff."""
        qs = super().get_queryset()
        user = getattr(self.request, 'user', None)

        if user is None or not user.is_authenticated:
            return qs.none()

        return qs

    @action(detail=True, methods=['get','post'], url_path='offers')
    def offers(self, request, pk=None):
        """Lista las ofertas asociadas a esta cotización. POST permite crear una nueva oferta."""
        quote = self.get_object()

        if request.method == 'GET':
            qs = quote.offers.all()
            status_filter = request.query_params.get('status')
            if status_filter:
                qs = qs.filter(status=status_filter)
            serializer = DeliveryOfferSerializer(qs, many=True, context={'request': request})
            return Response(serializer.data)

        if request.method == 'POST':
            if quote.status != 'pending':
                return Response({'error': 'No se pueden hacer ofertas sobre cotizaciones no pendientes'},
                                status=status.HTTP_400_BAD_REQUEST)

            existing = DeliveryOffer.objects.filter(quote=quote, delivery_person=request.user).first()
            data = request.data.copy()
            data['quote'] = str(quote.id)

            if existing:
                # actualizar campos permitidos
                serializer = DeliveryOfferSerializer(existing, data=data, partial=True, context={'request': request})
                if serializer.is_valid():
                    offer = serializer.save()
                    return Response(DeliveryOfferSerializer(offer, context={'request': request}).data,
                                    status=status.HTTP_200_OK)
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            # crear nueva oferta
            DeliveryHistory.objects.create(
                history_id=quote.history_id,
                event_type='offer_made',
                description='Nueva oferta creada por domiciliario',
                changed_by=request.user
            )

            data = request.data.copy()
            data['quote'] = str(quote.id)
            serializer = DeliveryOfferSerializer(data=data, context={'request': request})
            if serializer.is_valid():
                offer = serializer.save(delivery_person=request.user)
                return Response(DeliveryOfferSerializer(offer, context={'request': request}).data,
                                status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar una cotización y eliminar objetos relacionados"""
        quote = self.get_object()
        
        if quote.status != 'pending':
            return Response({'error': 'Solo se pueden cancelar cotizaciones pendientes'}, 
                           status=status.HTTP_400_BAD_REQUEST)
        
        quote.status = 'cancelled'
        quote.save()

        # Registrar en el historial antes de eliminar
        DeliveryHistory.objects.create(
            history_id=quote.history_id,
            event_type='cancelled',
            description='Cotización cancelada por el cliente',
            changed_by=request.user
        )

        serialized = DeliveryQuoteSerializer(quote, context={'request': request}).data

        # emitir broadcast para que clientes conectados actualicen UI
        _broadcast('new_quotes', {'type': 'quote_expired', 'data': serialized})
        _broadcast(f'quote_{str(quote.id)}', {'type': 'quote_expired', 'data': serialized})
        _broadcast(f'user_quotes_{quote.client_id}', {'type': 'quote_expired', 'data': serialized})

        return Response(serialized, status=status.HTTP_200_OK)

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