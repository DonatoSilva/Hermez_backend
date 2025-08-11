from .models import User, UserRating
from rest_framework import viewsets, permissions
from .serializers import UserSerializer, UserRatingSerializer

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.AllowAny] #TODO: buscar forma de validar con clerk framework

class UserRatingViewSet(viewsets.ModelViewSet):
    queryset = UserRating.objects.all()
    serializer_class = UserRatingSerializer
    permission_classes = [permissions.AllowAny] #TODO: buscar forma de validar con clerk framework

