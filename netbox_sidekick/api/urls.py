from django.urls import path
from rest_framework import routers
from .views import (
    DeviceCheckAccessView,
    NICListView,
)

router = routers.DefaultRouter()
urlpatterns = router.urls

urlpatterns += [
    path('nics/device/<int:device>/', NICListView.as_view(), name='nic_list_by_device'),
    path('device/access/<int:device>/', DeviceCheckAccessView.as_view(), name='nic_check_access'),
]
