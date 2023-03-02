from django.urls import path
from rest_framework import routers
from .views import (
    AccountingProfileViewSet,
    AccountingSourceViewSet,
    AllCurrentBandwidthView,
    BandwidthProfileViewSet,
    CurrentBandwidthView,
    DeviceCheckAccessView,
    FullMapViewSet,
    LogicalSystemViewSet,
    NetworkServiceTypeViewSet,
    NetworkServiceViewSet,
    NetworkServiceDeviceViewSet,
    NetworkServiceDuplicateInterfaces,
    NetworkServiceL2ViewSet,
    NetworkServiceL3ViewSet,
    NetworkServiceGroupViewSet,
    NetworkUsageListGroupsView,
    NetworkUsageListMembersView,
    NetworkUsageGroupView,
    NetworkUsageMemberView,
    NICListView,
    RoutingTypeViewSet,
)

router = routers.DefaultRouter()
router.register('map', FullMapViewSet, basename='map')
router.register('accountingprofile', AccountingProfileViewSet)
router.register('accountingsource', AccountingSourceViewSet)
router.register('bandwidthprofile', BandwidthProfileViewSet)
router.register('logicalsystem', LogicalSystemViewSet)
router.register('routingtype', RoutingTypeViewSet)
router.register('networkservicetype', NetworkServiceTypeViewSet)
router.register('networkservice', NetworkServiceViewSet)
router.register('networkservicedevice', NetworkServiceDeviceViewSet)
router.register('networkservicel2', NetworkServiceL2ViewSet)
router.register('networkservicel3', NetworkServiceL3ViewSet)
router.register('networkservicegroup', NetworkServiceGroupViewSet)
urlpatterns = router.urls

urlpatterns += [
    path('accounting_profiles/all_current_bandwidth',
         AllCurrentBandwidthView.as_view(), name='accounting_profile_all_current_bandwidth'),
    path('accounting_profiles/<int:profile>/current_bandwidth',
         CurrentBandwidthView.as_view(), name='accounting_profile_current_bandwidth'),
    path('device/access/<int:device>/', DeviceCheckAccessView.as_view(), name='nic_check_access'),
    # This should have a better name, but the "networkservice" namespace
    # is already used above.
    path('duplicate_interfaces/', NetworkServiceDuplicateInterfaces.as_view(), name='networkservice_duplicate_interfaces'),
    path('networkusage/groups/', NetworkUsageListGroupsView.as_view(), name='networkusage_groups'),
    path('networkusage/members/', NetworkUsageListMembersView.as_view(), name='networkusage_members'),
    path('networkusage/member/<int:member_id>/', NetworkUsageMemberView.as_view(), name='networkusage_member'),
    path('networkusage/group/<int:group_id>/', NetworkUsageGroupView.as_view(), name='networkusage_group'),
    path('nics/device/<int:device>/', NICListView.as_view(), name='nic_list_by_device'),
]
