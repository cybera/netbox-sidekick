from django.urls import path
from rest_framework import routers
from .views import (
    CurrentBandwidthView,
    DeviceCheckAccessView,
    FullMapViewSet,
    NetworkUsageListGroupsView,
    NetworkUsageListMembersView,
    NetworkUsageGroupView,
    NetworkUsageMemberView,
    NICListView,
)

router = routers.DefaultRouter()
router.register('map', FullMapViewSet, basename='map')
urlpatterns = router.urls

urlpatterns += [
    path('accounting_profiles/<int:profile>/current_bandwidth',
         CurrentBandwidthView.as_view(), name='accounting_profile_current_bandwidth'),
    path('device/access/<int:device>/', DeviceCheckAccessView.as_view(), name='nic_check_access'),
    path('networkusage/groups/', NetworkUsageListGroupsView.as_view(), name='networkusage_groups'),
    path('networkusage/members/', NetworkUsageListMembersView.as_view(), name='networkusage_members'),
    path('networkusage/member/<int:member_id>/', NetworkUsageMemberView.as_view(), name='networkusage_member'),
    path('networkusage/group/<int:group_id>/', NetworkUsageGroupView.as_view(), name='networkusage_group'),
    path('nics/device/<int:device>/', NICListView.as_view(), name='nic_list_by_device'),
]
