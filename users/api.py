from .models import User, UserRating
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from addresses.serializers import AddressSerializer
from .serializers import UserSerializer, UserRatingSerializer

class UserViewSet(viewsets.ModelViewSet):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = User.objects.filter(pk=self.request.user.pk)
        if user.exists():
            return user
        else:
            return Response({'error': 'User not found'}, status=status.HTTP_404_NOT_FOUND)

    def update(self, request, *args, **kwargs):
        if self.request.user.pk != kwargs.get('pk'):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return self.partial_update(request, *args, **kwargs)

    @action(detail=False, methods=['patch'], url_path='update', url_name='update-user')
    def update_user(self, request, pk=None):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({'message': f'User {user.userid} updated successfully'}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['get'], url_path='ratings')
    def ratings(self, request, pk=None):
        """
        GET /api/users/{pk}/ratings/ -> lista los UserRating recibidos por el usuario
        """
        user = self.get_object()
        ratings = user.received_ratings.all()
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)
    
    """
        GET /api/users/my-addresses/ -> lista las direcciones del usuario
        """
    @action(detail=True, methods=['get'], url_path='addresses')
    def addresses(self, request, pk=None):
        user = self.get_object()
        addresses = user.addresses.all()
        serializer = AddressSerializer(addresses, many=True, context=self.get_serializer_context())
        return Response(serializer.data)

class UserRatingViewSet(viewsets.ModelViewSet):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
