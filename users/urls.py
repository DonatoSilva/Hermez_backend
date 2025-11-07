from rest_framework import routers
from django.urls import include, path
from .api import UserViewSet, UserRatingViewSet
from .webhooks import clerk_webhook

router = routers.DefaultRouter()
router.register('me', UserViewSet, 'user')
router.register('user-ratings', UserRatingViewSet, 'user-ratings')

urlpatterns = [
    path('api/me/', include('addresses.urls')),
    path('api/me/', include('vehicles.urls')),
    path('api/', include(router.urls)),
    path("webhooks/clerk/", clerk_webhook, name="clerk_webhook"),
]