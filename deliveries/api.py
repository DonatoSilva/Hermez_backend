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
        """
        Avanzar automáticamente al siguiente estado del flujo del domicilio.
        Flujo: assigned -> picked_up -> in_transit -> delivered -> paid
        No permite avanzar a 'cancelled' (usar endpoint /cancel/ para eso)
        """
        delivery = self.get_object()
        
        # Definir el flujo de estados (sin incluir cancelled)
        STATUS_FLOW = {
            'assigned': 'picked_up',
            'picked_up': 'in_transit',
            'in_transit': 'delivered',
            'delivered': 'paid',
            'paid': None,  # Estado final, no hay siguiente
        }
        
        current_status = delivery.status
        
        # Validar que no esté cancelado
        if current_status == 'cancelled':
            return Response({
                'error': 'No se puede cambiar el estado de un domicilio cancelado'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Obtener el siguiente estado
        next_status = STATUS_FLOW.get(current_status)
        
        if next_status is None:
            return Response({
                'error': f'El domicilio ya está en el estado final: {delivery.get_status_display()}',
                'current_status': current_status
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Actualizar al siguiente estado
        old_status = delivery.status
        delivery.status = next_status
        delivery.save()
        
        # Registrar en el historial
        DeliveryHistory.objects.create(
            history_id=delivery.history_id,
            event_type='status_changed',
            description=f'Estado cambiado de {old_status} a {next_status}',
            changed_by=request.user
        )
        
        # Serializar el domicilio actualizado
        serialized = DeliverySerializer(delivery, context={'request': request}).data
        
        # Emitir broadcasts a los grupos relevantes
        delivery_id = str(delivery.id)
        client_id = delivery.client_id
        delivery_person_id = delivery.delivery_person_id
        
        payload = {'type': 'delivery_status_changed', 'data': serialized}
        
        # Broadcast a grupos específicos
        _broadcast(f'delivery_{delivery_id}', payload)
        
        if client_id:
            _broadcast(f'user_deliveries_{client_id}', payload)
        
        if delivery_person_id:
            _broadcast(f'driver_deliveries_{delivery_person_id}', payload)
        
        return Response({
            'message': f'Estado actualizado de {old_status} a {next_status}',
            'old_status': old_status,
            'new_status': next_status,
            'delivery': serialized
        }, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancelar un domicilio y notificar a todos los WebSockets relevantes"""
        delivery = self.get_object()
        
        # Validar que el domicilio no esté ya en un estado final
        if delivery.status in ['delivered', 'paid', 'cancelled']:
            return Response({
                'error': f'No se puede cancelar un domicilio en estado "{delivery.get_status_display()}"'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Guardar datos antes de actualizar para los broadcasts
        delivery_id = str(delivery.id)
        client_id = delivery.client_id
        delivery_person_id = delivery.delivery_person_id
        old_status = delivery.status
        
        # Actualizar estado a cancelado
        delivery.status = 'cancelled'
        delivery.save()  # Esto también actualizará cancelled_at mediante el método save() del modelo
        
        # Registrar en el historial
        DeliveryHistory.objects.create(
            history_id=delivery.history_id,
            event_type='cancelled',
            description=f'Domicilio cancelado (estado anterior: {old_status})',
            changed_by=request.user
        )
        
        # Serializar el domicilio actualizado
        serialized = DeliverySerializer(delivery, context={'request': request}).data
        
        # Broadcasts a todos los grupos relevantes
        payload = {'type': 'delivery_cancelled', 'data': serialized}
        
        # 1. Grupo específico del domicilio
        _broadcast(f'delivery_{delivery_id}', payload)
        
        # 2. Grupo del cliente (user_deliveries) - el domicilio desaparece de su lista
        if client_id:
            _broadcast(f'user_deliveries_{client_id}', payload)
        
        # 3. Grupo del domiciliario (driver_deliveries) - el domicilio desaparece de su lista
        if delivery_person_id:
            _broadcast(f'driver_deliveries_{delivery_person_id}', payload)
        
        return Response({
            'message': 'Domicilio cancelado exitosamente',
            'delivery': serialized
        }, status=status.HTTP_200_OK)


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

        # Serializar antes de eliminar
        quote_payload = DeliveryQuoteSerializer(offer.quote, context={'request': request}).data
        delivery_payload = DeliverySerializer(delivery, context={'request': request}).data
        
        # Guardar IDs antes de eliminar
        quote_id = str(offer.quote.id)
        client_id = offer.quote.client_id
        
        # Broadcasts para notificar que la cotización fue aceptada y se eliminará
        _broadcast(f'quote_{quote_id}', {'type': 'quote_accepted', 'data': quote_payload})
        _broadcast(f'user_quotes_{client_id}', {'type': 'quote_accepted', 'data': quote_payload})
        _broadcast(f'new_quotes', {'type': 'quote_accepted', 'data': quote_payload})
        
        # Notificar creación del domicilio
        _broadcast(f'user_deliveries_{delivery.client_id}', {'type': 'delivery_created', 'data': delivery_payload})
        
        # Notificar al domiciliario asignado
        if delivery.delivery_person_id:
            _broadcast(f'driver_deliveries_{delivery.delivery_person_id}', {'type': 'delivery_assigned', 'data': delivery_payload})
        
        # Eliminar la cotización y todas sus ofertas (cascade)
        offer.quote.delete()  # Esto también elimina todas las ofertas relacionadas por cascade
        
        return Response({
            'message': 'Oferta aceptada y domicilio creado',
            'delivery_id': str(delivery.id),
            'delivery': delivery_payload,
            'quote_deleted': True
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

        # Registrar en el historial antes de eliminar
        DeliveryHistory.objects.create(
            history_id=quote.history_id,
            event_type='cancelled',
            description='Cotización cancelada por el cliente',
            changed_by=request.user
        )

        serialized = DeliveryQuoteSerializer(quote, context={'request': request}).data

        # Guardar identificadores antes de eliminar definitivamente el registro
        quote_id = str(quote.id)
        client_id = quote.client_id

        # Eliminar la cotización (y sus ofertas relacionadas vía cascade)
        quote.delete()

        # Emitir broadcast para que clientes conectados actualicen UI
        payload = {'type': 'quote_expired', 'data': serialized}
        _broadcast('new_quotes', payload)
        _broadcast(f'quote_{quote_id}', payload)
        _broadcast(f'user_quotes_{client_id}', payload)

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