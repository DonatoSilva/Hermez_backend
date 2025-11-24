from .models import User, UserRating
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import UserSerializer, UserRatingSerializer
from users.authentication import ClerkAuthentication
from vehicles.models import Vehicle

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    authentication_classes = [ClerkAuthentication]

    def get_queryset(self):
        if self.request.user.is_authenticated:
            return User.objects.filter(pk=self.request.user.pk)
        else:
            return User.objects.none()

    ## Funciones para la gestion del usuario: se busca que solo el propio usuario pueda actualizar o eliminar su perfil
    def update(self, request, *args, **kwargs):
        """
        PATCH /api/users/{pk}/ -> actualiza los datos del usuario autenticado /// se modifico el comportamiento por defecto
        """
        if self.request.user.pk != kwargs.get('pk'):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return self.partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['patch'], url_path='update', url_name='update-user')
    def update_user(self, request, pk=None):
        """
        PATCH /api/users/update/ -> actualiza los datos del usuario autenticado
        """
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': f'User {user.userid} updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/users/{pk}/ -> elimina el perfil del usuario autenticado /// se modifico el comportamiento por defecto
        """
        if self.request.user.pk != kwargs.get('pk'):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)

    @action(detail=False, methods=['post'], url_path='toggle-availability')
    def toggle_availability(self, request):
        user = request.user
        new_state = user.toggle_availability()
        return Response({'is_available': new_state}, status=status.HTTP_200_OK)

        
    @action(detail=True, methods=['get'], url_path='ratings')
    def ratings(self, request, pk=None):
        """
        GET /api/users/{pk}/ratings/ -> lista los UserRating recibidos por el usuario
        """
        user = self.get_object()
        ratings = user.received_ratings.all()
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'], url_path='set-current-vehicle')
    def set_current_vehicle(self, request):
        """
        POST /api/me/set-current-vehicle/ -> establece `current_vehicle` del usuario autenticado.
        Payload: { "vehicle_id": "<uuid>" }
        Validaciones:
        - `vehicle_id` no puede venir vacío
        - el vehículo debe pertenecer al usuario autenticado
        """
        user = request.user
        vehicle_id = request.data.get('vehicle_id') or request.data.get('vehicleId')

        if not vehicle_id:
            return Response({'vehicle_id': 'Este campo es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            vehicle = Vehicle.objects.get(vehicleId=vehicle_id)
        except Vehicle.DoesNotExist:
            return Response({'vehicle_id': 'Vehículo no encontrado.'}, status=status.HTTP_404_NOT_FOUND)

        # Verificar pertenencia: el vehículo debe pertenecer al usuario autenticado
        if vehicle.userId_id != getattr(user, 'userid', None):
            return Response({'detail': 'El vehículo no pertenece al usuario autenticado.'}, status=status.HTTP_403_FORBIDDEN)

        # Si el vehículo enviado es el mismo que el actual, deseleccionarlo (poner a null)
        if getattr(user, 'current_vehicle_id', None) == vehicle.vehicleId:
            user.current_vehicle = None
            user.save(update_fields=['current_vehicle'])
            return Response({'message': 'Vehículo deseleccionado correctamente', 'vehicle_id': None}, status=status.HTTP_200_OK)

        # Asignar y guardar
        user.current_vehicle = vehicle
        user.save(update_fields=['current_vehicle'])

        return Response({'message': 'Vehículo actual establecido correctamente', 'vehicle_id': str(vehicle.vehicleId)}, status=status.HTTP_200_OK)

class UserRatingViewSet(viewsets.ModelViewSet):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
