from rest_framework import routers
from .api import AddressViewSet

router = routers.DefaultRouter()
router.register('api/addresses', AddressViewSet, 'addresses')

urlpatterns = router.urls
