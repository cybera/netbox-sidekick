from django.urls import path

from . import views

urlpatterns = [
    # Accounting Profile Index
    path('accounting_profiles/', views.AccountingProfileIndexView.as_view(), name='accountingprofile_index'),

    # Accounting Profile Details
    path('accounting_profiles/<int:pk>/', views.AccountingProfileDetailView.as_view(), name='accountingprofile_detail'),

    # Accounting Class Index
    path('accounting_classes/', views.AccountingClassIndexView.as_view(), name='accountingclass_index'),

    # Accounting Class Details
    path('accounting_classes/<int:pk>/', views.AccountingClassDetailView.as_view(), name='accountingclass_detail'),

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

    # Logical System Index
    path('logical_systems/', views.LogicalSystemIndexView.as_view(), name='logicalsystem_index'),

    # Logical System Details
    path('logical_systems/<slug:slug>/', views.LogicalSystemDetailView.as_view(), name='logicalsystem_detail'),

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

    # NIC Index
    path('nics/', views.NICIndexView.as_view(), name='nic_index'),

    # NIC Details
    path('nics/<int:pk>', views.NICDetailView.as_view(), name='nic_detail'),

    # Routing Type Index
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_index'),

    # Routing Type Details
    path('routing_types/<slug:slug>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),
]
