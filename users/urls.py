from rest_framework import routers
from django.urls import include, path
from .api import UserViewSet, UserRatingViewSet

router = routers.DefaultRouter()
router.register('me', UserViewSet, 'user')
router.register('user-ratings', UserRatingViewSet, 'user-ratings')

urlpatterns = [
    path('api/', include(router.urls)),
    path('api/users/', include('addresses.urls')),
]