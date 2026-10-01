from django.urls import include, path

from utilities.urls import get_model_urls

from . import views

urlpatterns = [
    # Accounting profiles
    path('accounting_profiles/', include(get_model_urls('sidekick', 'accountingprofile', detail=False))),
    path('accounting_profiles/<int:pk>/', include(get_model_urls('sidekick', 'accountingprofile'))),

    # Accounting sources
    path('accounting_sources/', include(get_model_urls('sidekick', 'accountingsource', detail=False))),
    path('accounting_sources/<int:pk>/', include(get_model_urls('sidekick', 'accountingsource'))),

    # Bandwidth profiles
    path('bandwidth_profiles/', include(get_model_urls('sidekick', 'bandwidthprofile', detail=False))),
    path('bandwidth_profiles/<int:pk>/', include(get_model_urls('sidekick', 'bandwidthprofile'))),

    # Logical systems
    path('logical_systems/', include(get_model_urls('sidekick', 'logicalsystem', detail=False))),
    path('logical_systems/<int:pk>/', include(get_model_urls('sidekick', 'logicalsystem'))),

    # Routing types
    path('routing_types/', include(get_model_urls('sidekick', 'routingtype', detail=False))),
    path('routing_types/<int:pk>/', include(get_model_urls('sidekick', 'routingtype'))),

    # Network service types
    path('network_service_types/', include(get_model_urls('sidekick', 'networkservicetype', detail=False))),
    path('network_service_types/<int:pk>/', include(get_model_urls('sidekick', 'networkservicetype'))),

    # Network services
    path('network_services/', include(get_model_urls('sidekick', 'networkservice', detail=False))),
    path('network_services/<int:pk>/', include(get_model_urls('sidekick', 'networkservice'))),

    # Network service devices
    path('network_service_devices/', include(get_model_urls('sidekick', 'networkservicedevice', detail=False))),
    path('network_service_devices/<int:pk>/', include(get_model_urls('sidekick', 'networkservicedevice'))),

    # Network service L2
    path('network_service_l2/', include(get_model_urls('sidekick', 'networkservicel2', detail=False))),
    path('network_service_l2/<int:pk>/', include(get_model_urls('sidekick', 'networkservicel2'))),

    # Network service L3
    path('network_services_l3/', include(get_model_urls('sidekick', 'networkservicel3', detail=False))),
    path('network_services_l3/<int:pk>/', include(get_model_urls('sidekick', 'networkservicel3'))),

    # Network service groups
    path('network_service_groups/', include(get_model_urls('sidekick', 'networkservicegroup', detail=False))),
    path('network_service_groups/<int:pk>/', include(get_model_urls('sidekick', 'networkservicegroup'))),

    # NICs
    path('nics/', include(get_model_urls('sidekick', 'nic', detail=False))),
    path('nics/<int:pk>/', include(get_model_urls('sidekick', 'nic'))),

    # Peering connections (read-only filtered list of L3 services)
    path('peering_connections/', views.PeeringConnectionListView.as_view(), name='peeringconnection_list'),

    # Member bandwidth report
    path('member_bandwidth/', views.MemberBandwidthIndexView.as_view(), name='memberbandwidth_index'),
    path('member_bandwidth/<int:pk>/', views.MemberBandwidthDetailView.as_view(), name='memberbandwidth_detail'),
    path('member_bandwidth/graphite/<int:pk>', views.MemberBandwidthDataView.as_view(), name='memberbandwidth_data'),

    # Member contacts
    path('member_contacts/', views.MemberContactsView.as_view(), name='membercontact_list'),

    # Graph data endpoints
    path('network_service/graphite/<int:pk>', views.NetworkServiceGraphiteDataView.as_view(),
         name='network_service_graphite_data'),
    path('network_service_groups/graphite/<int:pk>', views.NetworkServiceGroupGraphiteDataView.as_view(),
         name='networkservicegroup_data'),
    path('nics/graphite/<int:pk>', views.NICGraphiteDataView.as_view(), name='nic_graphite_data'),
]
