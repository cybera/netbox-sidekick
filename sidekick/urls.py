from django.urls import path

from . import views

urlpatterns = [
    # Accounting Profile Index
    path('accounting_profiles/', views.AccountingProfileIndexView.as_view(), name='accountingprofile_list'),

    # Accounting Profile Details
    path('accounting_profiles/<int:pk>/', views.AccountingProfileDetailView.as_view(), name='accountingprofile_detail'),

    # Accounting Profile Edit
    path('accounting_profiles/<int:pk>/edit/', views.AccountingProfileEditView.as_view(), name='accountingprofile_edit'),

    # Accounting Profile Delete
    path('accounting_profiles/<int:pk>/delete/', views.AccountingProfileDeleteView.as_view(), name='accountingprofile_delete'),

    # Accounting Source Index
    path('accounting_sources/', views.AccountingSourceIndexView.as_view(), name='accountingsource_list'),

    # Accounting Source Details
    path('accounting_sources/<int:pk>/', views.AccountingSourceDetailView.as_view(), name='accountingsource_detail'),

    # Accounting Source Edit
    path('accounting_sources/<int:pk>/edit/', views.AccountingSourceEditView.as_view(), name='accountingsource_edit'),

    # Accounting Source Delete
    path('accounting_sources/<int:pk>/delete/', views.AccountingSourceDeleteView.as_view(), name='accountingsource_delete'),

    # Bandwidth Profile Index
    path('bandwidth_profiles/', views.BandwidthProfileIndexView.as_view(), name='bandwidthprofile_list'),

    # Bandwidth Profile Details
    path('bandwidth_profiles/<int:pk>/', views.BandwidthProfileDetailView.as_view(), name='bandwidthprofile_detail'),

    # Bandwidth Profile Edit
    path('bandwidth_profiles/<int:pk>/edit/', views.BandwidthProfileEditView.as_view(), name='bandwidthprofile_edit'),

    # Bandwidth Profile Delete
    path('bandwidth_profiles/<int:pk>/delete/', views.BandwidthProfileDeleteView.as_view(), name='bandwidthprofile_delete'),

    # IP Prefix Index
    path('ip_prefixes/', views.IPPrefixIndexView.as_view(), name='ipprefix_index'),

    # Logical System Index
    path('logical_systems/', views.LogicalSystemIndexView.as_view(), name='logicalsystem_list'),

    # Logical System Details
    path('logical_systems/<int:pk>/', views.LogicalSystemDetailView.as_view(), name='logicalsystem_detail'),

    # Logical System Edit
    path('logical_systems/<int:pk>/edit/', views.LogicalSystemEditView.as_view(), name='logicalsystem_edit'),

    # Logical System Delete
    path('logical_systems/<int:pk>/delete/', views.LogicalSystemDeleteView.as_view(), name='logicalsystem_delete'),

    # Member Create
    path('member/create', views.MemberCreateView.as_view(), name='member_create'),

    # Member Bandwidth Report Index
    path('member_bandwidth/', views.MemberBandwidthIndexView.as_view(), name='memberbandwidth_index'),

    # Member Bandwidth Report Details
    path('member_bandwidth/<int:pk>/', views.MemberBandwidthDetailView.as_view(), name='memberbandwidth_detail'),

    # Member Bandwidth Data
    path('member_bandwidth/graphite/<int:pk>', views.MemberBandwidthDataView.as_view(), name='memberbandwidth_data'),

    # Network Service Type Index
    path('network_service_types/', views.NetworkServiceTypeIndexView.as_view(), name='networkservicetype_list'),

    # Network Service Type Details
    path('network_service_types/<int:pk>/', views.NetworkServiceTypeDetailView.as_view(), name='networkservicetype_detail'),

    # Network Service Type Edit
    path('network_service_types/<int:pk>/edit/', views.NetworkServiceTypeEditView.as_view(), name='networkservicetype_edit'),

    # Network Service Type Delete
    path('network_service_types/<int:pk>/delete/', views.NetworkServiceTypeDeleteView.as_view(), name='networkservicetype_delete'),

    # Network Service Index
    path('network_services/', views.NetworkServiceIndexView.as_view(), name='networkservice_list'),

    # Network Service Details
    path('network_services/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservice_detail'),

    # Network Service Edit
    path('network_services/<int:pk>/edit', views.NetworkServiceEditView.as_view(), name='networkservice_edit'),

    # Network Service Delete
    path('network_services/<int:pk>/delete', views.NetworkServiceDeleteView.as_view(), name='networkservice_delete'),

    # Network Service Graphite data
    path('network_service/graphite/<int:pk>', views.NetworkServiceGraphiteDataView.as_view(), name='network_service_graphite_data'),

    # Network Service Device Index
    path('network_service_devices/', views.NetworkServiceIndexView.as_view(), name='networkservicedevice_list'),

    # Network Service Device Details
    path('network_service_devices/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservicedevice_detail'),

    # Network Service Group Index
    path('network_service_groups/', views.NetworkServiceGroupIndexView.as_view(), name='networkservicegroup_list'),

    # Network Service Group Details
    path('network_service_groups/<int:pk>/', views.NetworkServiceGroupDetailView.as_view(), name='networkservicegroup_detail'),

    # Network Service Group Edit
    path('network_service_groups/<int:pk>/edit/', views.NetworkServiceGroupEditView.as_view(), name='networkservicegroup_edit'),

    # Network Service Group Delete
    path('network_service_groups/<int:pk>/delete/', views.NetworkServiceGroupDeleteView.as_view(), name='networkservicegroup_delete'),

    # Network Service Group Graphite Data
    path('network_service_groups/graphite/<int:pk>', views.NetworkServiceGroupGraphiteDataView.as_view(), name='networkservicegroup_data'),

    # NIC Index
    path('nics/', views.NICIndexView.as_view(), name='nic_list'),

    # NIC Details
    path('nics/<int:interface__id>/', views.NICDetailView.as_view(), name='nic_detail'),

    # NIC Edit
    path('nics/<int:pk>/edit/', views.NICEditView.as_view(), name='nic_edit'),

    # NIC Delete
    path('nics/<int:pk>/delete/', views.NICDeleteView.as_view(), name='nic_delete'),

    # NIC Graphite data
    path('nics/graphite/<int:pk>', views.NICGraphiteDataView.as_view(), name='nic_graphite_data'),

    # Routing Type Index
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_list'),

    # Routing Type Details
    path('routing_types/<int:pk>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),

    # Routing Type Edit
    path('routing_types/<int:pk>/edit/', views.RoutingTypeEditView.as_view(), name='routingtype_edit'),

    # Routing Type Delete
    path('routing_types/<int:pk>/delete/', views.RoutingTypeDeleteView.as_view(), name='routingtype_delete'),
]
