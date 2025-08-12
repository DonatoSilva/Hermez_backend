from rest_framework import routers
from .api import UserViewSet, UserRatingViewSet

router = routers.DefaultRouter()
router.register('api/users', UserViewSet, 'users')
router.register('api/user-ratings', UserRatingViewSet, 'user-ratings')

urlpatterns = router.urls