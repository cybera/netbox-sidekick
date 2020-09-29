from django.urls import path
from rest_framework import routers
from .views import (
    FullMapViewSet, MemberViewSet,
    NICListView,
)

router = routers.DefaultRouter()
router.register('map', FullMapViewSet, basename='map')
router.register('members', MemberViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('nics/device/<int:device>/', NICListView.as_view(), name='nic_list_by_device'),
]
