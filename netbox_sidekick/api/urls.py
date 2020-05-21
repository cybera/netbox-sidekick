from rest_framework import routers
from .views import MemberViewSet, FullMapViewSet

router = routers.DefaultRouter()
router.register('members', MemberViewSet)
router.register('map', FullMapViewSet, basename='map')
urlpatterns = router.urls
