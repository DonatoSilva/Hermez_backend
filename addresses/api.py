from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Address
from .serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        if self.request.user and self.request.user.is_authenticated:
            return Address.objects.filter(userId=self.request.user)
        return Address.objects.none()

    def perform_create(self, serializer):
        serializer.save(userId=self.request.user)

    @action(detail=True, methods=['post'], url_path='add-favorite')
    def add_favorite(self, request, pk=None):
        """
        POST /addresses/<pk>/add-favorite/ -> agrega una dirección a favoritos
        """
        address = self.get_object()
        address.isFavorite = not address.isFavorite
        address.save()
        return Response({'message': 'Dirección agregada a favoritos' if address.isFavorite else 'Dirección eliminada de favoritos', 'isFavorite': address.isFavorite}, status=status.HTTP_200_OK)
