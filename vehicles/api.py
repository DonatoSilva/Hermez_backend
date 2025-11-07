from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Vehicle
from .serializers import VehicleSerializer

class VehicleViewSet(viewsets.ModelViewSet):
    serializer_class = VehicleSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            return Vehicle.objects.filter(userId=self.request.user)
        return Vehicle.objects.none()

    def perform_create(self, serializer):
        serializer.save(userId=self.request.user)

    def update(self, request, *args, **kwargs):
        """
        PUT/PATCH /api/me/vehicles/{pk}/ -> actualiza un vehículo del usuario autenticado
        """
        if self.request.user.pk != self.get_object().userId.pk:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/me/vehicles/{pk}/ -> elimina un vehículo del usuario autenticado
        """
        if self.request.user.pk != self.get_object().userId.pk:
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)