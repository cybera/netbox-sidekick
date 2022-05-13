from django.urls import path

from . import views

urlpatterns = [
    # Accounting Profile
    path('accounting_profiles/', views.AccountingProfileIndexView.as_view(), name='accountingprofile_list'),
    path('accounting_profiles/add/', views.AccountingProfileEditView.as_view(), name='accountingprofile_add'),
    path('accounting_profiles/<int:pk>/', views.AccountingProfileDetailView.as_view(), name='accountingprofile_detail'),
    path('accounting_profiles/<int:pk>/edit/', views.AccountingProfileEditView.as_view(), name='accountingprofile_edit'),
    path('accounting_profiles/<int:pk>/delete/', views.AccountingProfileDeleteView.as_view(), name='accountingprofile_delete'),

    # Accounting Source
    path('accounting_sources/', views.AccountingSourceIndexView.as_view(), name='accountingsource_list'),
    path('accounting_sources/<int:pk>/', views.AccountingSourceDetailView.as_view(), name='accountingsource_detail'),

    # Bandwidth Profile
    path('bandwidth_profiles/', views.BandwidthProfileIndexView.as_view(), name='bandwidthprofile_list'),
    path('bandwidth_profiles/add/', views.BandwidthProfileEditView.as_view(), name='bandwidthprofile_add'),
    path('bandwidth_profiles/<int:pk>/', views.BandwidthProfileDetailView.as_view(), name='bandwidthprofile_detail'),
    path('bandwidth_profiles/<int:pk>/edit/', views.BandwidthProfileEditView.as_view(), name='bandwidthprofile_edit'),
    path('bandwidth_profiles/<int:pk>/delete/', views.BandwidthProfileDeleteView.as_view(), name='bandwidthprofile_delete'),

    # IP Prefix
    path('ip_prefixes/', views.IPPrefixIndexView.as_view(), name='ipprefix_index'),

    # Logical System
    path('logical_systems/', views.LogicalSystemIndexView.as_view(), name='logicalsystem_list'),
    path('logical_systems/add/', views.LogicalSystemEditView.as_view(), name='logicalsystem_add'),
    path('logical_systems/<int:pk>/', views.LogicalSystemDetailView.as_view(), name='logicalsystem_detail'),
    path('logical_systems/<int:pk>/edit/', views.LogicalSystemEditView.as_view(), name='logicalsystem_edit'),
    path('logical_systems/<int:pk>/delete/', views.LogicalSystemDeleteView.as_view(), name='logicalsystem_delete'),

    # Member Bandwidth Report Index
    path('member_bandwidth/', views.MemberBandwidthIndexView.as_view(), name='memberbandwidth_index'),

    # Member Bandwidth Report Details
    path('member_bandwidth/<int:pk>/', views.MemberBandwidthDetailView.as_view(), name='memberbandwidth_detail'),

    # Member Bandwidth Data
    path('member_bandwidth/graphite/<int:pk>', views.MemberBandwidthDataView.as_view(), name='memberbandwidth_data'),

    # Member Contacts
    path('member_contacts/', views.MemberContactsView.as_view(), name='membercontact_list'),

    # Network Service Type
    path('network_service_types/', views.NetworkServiceTypeIndexView.as_view(), name='networkservicetype_list'),
    path('network_service_types/add/', views.NetworkServiceTypeEditView.as_view(), name='networkservicetype_add'),
    path('network_service_types/<int:pk>/', views.NetworkServiceTypeDetailView.as_view(), name='networkservicetype_detail'),
    path('network_service_types/<int:pk>/edit/', views.NetworkServiceTypeEditView.as_view(), name='networkservicetype_edit'),
    path('network_service_types/<int:pk>/delete/', views.NetworkServiceTypeDeleteView.as_view(), name='networkservicetype_delete'),

    # Network Service
    path('network_services/', views.NetworkServiceIndexView.as_view(), name='networkservice_list'),
    path('network_services/add/', views.NetworkServiceEditView.as_view(), name='networkservice_add'),
    path('network_services/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservice_detail'),
    path('network_services/<int:pk>/edit', views.NetworkServiceEditView.as_view(), name='networkservice_edit'),
    path('network_services/<int:pk>/delete', views.NetworkServiceDeleteView.as_view(), name='networkservice_delete'),

    # Network Service Graphite data
    path('network_service/graphite/<int:pk>', views.NetworkServiceGraphiteDataView.as_view(), name='network_service_graphite_data'),

    # Network Service Device Index
    path('network_service_devices/', views.NetworkServiceIndexView.as_view(), name='networkservicedevice_list'),

    # Network Service Device Details
    path('network_service_devices/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservicedevice_detail'),

    # Network Service Group
    path('network_service_groups/', views.NetworkServiceGroupIndexView.as_view(), name='networkservicegroup_list'),
    path('network_service_groups/add/', views.NetworkServiceGroupEditView.as_view(), name='networkservicegroup_add'),
    path('network_service_groups/<int:pk>/', views.NetworkServiceGroupDetailView.as_view(), name='networkservicegroup_detail'),
    path('network_service_groups/<int:pk>/edit/', views.NetworkServiceGroupEditView.as_view(), name='networkservicegroup_edit'),
    path('network_service_groups/<int:pk>/delete/', views.NetworkServiceGroupDeleteView.as_view(), name='networkservicegroup_delete'),

    # Network Service Group Graphite Data
    path('network_service_groups/graphite/<int:pk>', views.NetworkServiceGroupGraphiteDataView.as_view(), name='networkservicegroup_data'),

    # NIC
    path('nics/', views.NICIndexView.as_view(), name='nic_list'),
    path('nics/add/', views.NICEditView.as_view(), name='nic_add'),
    path('nics/<int:interface__id>/', views.NICDetailView.as_view(), name='nic_detail'),
    path('nics/<int:pk>/edit/', views.NICEditView.as_view(), name='nic_edit'),
    path('nics/<int:pk>/delete/', views.NICDeleteView.as_view(), name='nic_delete'),

    # NIC Graphite data
    path('nics/graphite/<int:pk>', views.NICGraphiteDataView.as_view(), name='nic_graphite_data'),

    # Routing Type
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_list'),
    path('routing_types/add/', views.RoutingTypeEditView.as_view(), name='routingtype_add'),
    path('routing_types/<int:pk>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),
    path('routing_types/<int:pk>/edit/', views.RoutingTypeEditView.as_view(), name='routingtype_edit'),
    path('routing_types/<int:pk>/delete/', views.RoutingTypeDeleteView.as_view(), name='routingtype_delete'),
]
