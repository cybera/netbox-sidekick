from django.urls import path

from . import views

urlpatterns = [
    # Accounting Profile Index
    path('accounting_profiles/', views.AccountingProfileIndexView.as_view(), name='accountingprofile_index'),

    # Accounting Profile Details
    path('accounting_profiles/<int:pk>/', views.AccountingProfileDetailView.as_view(), name='accountingprofile_detail'),

    # Accounting Source Index
    path('accounting_sources/', views.AccountingSourceIndexView.as_view(), name='accountingsource_index'),

    # Accounting Source Details
    path('accounting_sources/<int:pk>/', views.AccountingSourceDetailView.as_view(), name='accountingsource_detail'),

    # Bandwidth Profile Index
    path('bandwidth_profiles/', views.BandwidthProfileIndexView.as_view(), name='bandwidthprofile_index'),

    # Bandwidth Profile Details
    path('bandwidth_profiles/<int:pk>/', views.BandwidthProfileDetailView.as_view(), name='bandwidthprofile_detail'),

    # Contact Type Index
    path('contact_types/', views.ContactTypeIndexView.as_view(), name='contacttype_index'),

    # Contact Type Details
    path('contact_types/<slug:slug>/', views.ContactTypeDetailView.as_view(), name='contacttype_detail'),

    # Contact Index
    path('contacts/', views.ContactIndexView.as_view(), name='contact_index'),

    # Contact Details
    path('contacts/<int:pk>/', views.ContactDetailView.as_view(), name='contact_detail'),

    # IP Prefix Index
    path('ip_prefixes/', views.IPPrefixIndexView.as_view(), name='ipprefix_index'),

    # Logical System Index
    path('logical_systems/', views.LogicalSystemIndexView.as_view(), name='logicalsystem_index'),

    # Logical System Details
    path('logical_systems/<slug:slug>/', views.LogicalSystemDetailView.as_view(), name='logicalsystem_detail'),

    # Member Bandwidth Report Index
    path('member_bandwidth/', views.MemberBandwidthIndexView.as_view(), name='memberbandwidth_index'),

    # Member Bandwidth Report Details
    path('member_bandwidth/<int:pk>/', views.MemberBandwidthDetailView.as_view(), name='memberbandwidth_detail'),

    # Member Bandwidth Services Data
    path('member_bandwidth/graphite/services/<int:pk>', views.MemberBandwidthServicesDataView.as_view(), name='memberbandwidth_services_data'),

    # Member Bandwidth Accounting Data
    path('member_bandwidth/graphite/accounting/<int:pk>', views.MemberBandwidthAccountingDataView.as_view(), name='memberbandwidth_accounting_data'),

    # Member Bandwidth Remaining Data
    path('member_bandwidth/graphite/remaining/<int:pk>', views.MemberBandwidthRemainingDataView.as_view(), name='memberbandwidth_remaining_data'),

    # Member Bandwidth Data
    path('member_bandwidth/graphite/<int:pk>', views.MemberBandwidthDataView.as_view(), name='memberbandwidth_data'),

    # Network Service Type Index
    path('network_service_types/', views.NetworkServiceTypeIndexView.as_view(), name='networkservicetype_index'),

    # Network Service Type Details
    path('network_service_types/<slug:slug>/', views.NetworkServiceTypeDetailView.as_view(), name='networkservicetype_detail'),

    # Network Service Index
    path('network_services/', views.NetworkServiceIndexView.as_view(), name='networkservice_index'),

    # Network Service Details
    path('network_services/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservice_detail'),

    # Network Service Device Index
    path('network_service_devices/', views.NetworkServiceIndexView.as_view(), name='networkservicedevice_index'),

    # Network Service Device Details
    path('network_service_devices/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservicedevice_detail'),

    # Network Service Group Index
    path('network_service_groups/', views.NetworkServiceGroupIndexView.as_view(), name='networkservicegroup_index'),

    # Network Service Group Details
    path('network_service_groups/<int:pk>/', views.NetworkServiceGroupDetailView.as_view(), name='networkservicegroup_detail'),

    # Network Service Graphite data
    path('network_service/graphite/<int:pk>', views.NetworkServiceGraphiteDataView.as_view(), name='network_service_graphite_data'),

    # NIC Index
    path('nics/', views.NICIndexView.as_view(), name='nic_index'),

    # NIC Details
    path('nics/<int:pk>', views.NICDetailView.as_view(), name='nic_detail'),

    # NIC Graphite data
    path('nics/graphite/<int:pk>', views.NICGraphiteDataView.as_view(), name='nic_graphite_data'),

    # Routing Type Index
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_index'),

    # Routing Type Details
    path('routing_types/<slug:slug>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),
]
