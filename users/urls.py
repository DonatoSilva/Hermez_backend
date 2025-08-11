from rest_framework import routers
from .api import UserViewSet, UserRatingViewSet

routers = routers.DefaultRouter()
routers.register('api/users', UserViewSet, 'users')
routers.register('api/user-ratings', UserRatingViewSet, 'user-ratings')

urlpatterns = routers.urls