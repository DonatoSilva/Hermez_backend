from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Address
from .serializers import AddressSerializer


class AddressViewSet(viewsets.ModelViewSet):
    queryset = Address.objects.all()
    serializer_class = AddressSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=True, methods=['post'], url_path='add-favorite')
    def add_favorite(self, request, pk=None):
        """
        POST /addresses/<pk>/add-favorite/ -> agrega una dirección a favoritos
        """
        address = self.get_object()
        address.isFavorite = True
        address.save()
        return Response({'message': 'Dirección agregada a favoritos'}, status=status.HTTP_200_OK)