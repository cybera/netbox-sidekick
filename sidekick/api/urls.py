from django.urls import path
from rest_framework import routers
from .views import (
    DeviceCheckAccessView,
    FullMapViewSet,
    NICListView,
)

router = routers.DefaultRouter()
router.register('map', FullMapViewSet, basename='map')
urlpatterns = router.urls

urlpatterns += [
    path('device/access/<int:device>/', DeviceCheckAccessView.as_view(), name='nic_check_access'),
    path('nics/device/<int:device>/', NICListView.as_view(), name='nic_list_by_device'),
]
