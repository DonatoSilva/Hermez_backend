from .models import User, UserRating
from rest_framework import status, viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from addresses.serializers import AddressSerializer
from .serializers import UserSerializer, UserRatingSerializer
from users.authentication import ClerkAuthentication

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
            print(serializer.errors)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, *args, **kwargs):
        """
        DELETE /api/users/{pk}/ -> elimina el perfil del usuario autenticado /// se modifico el comportamiento por defecto
        """
        if self.request.user.pk != kwargs.get('pk'):
            return Response({'error': 'Access denied'}, status=status.HTTP_403_FORBIDDEN)
        return super().destroy(request, *args, **kwargs)


    @action(detail=False, methods=['delete'], url_path='delete', url_name='delete-user')
    def delete_user(self, request):
        """
        DELETE /api/me/delete/ -> elimina el perfil del usuario autenticado
        """
        try:
            user = request.user
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    @action(detail=True, methods=['get'], url_path='ratings')
    def ratings(self, request, pk=None):
        """
        GET /api/users/{pk}/ratings/ -> lista los UserRating recibidos por el usuario
        """
        user = self.get_object()
        ratings = user.received_ratings.all()
        serializer = self.get_serializer(ratings, many=True)
        return Response(serializer.data)

class UserRatingViewSet(viewsets.ModelViewSet):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.IsAuthenticated]
