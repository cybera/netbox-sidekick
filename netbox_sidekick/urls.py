from django.urls import path

from . import views

urlpatterns = [
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

    # Network Service Connection Type Index
    path('network_service_connection_types/', views.NetworkServiceConnectionTypeIndexView.as_view(), name='networkserviceconnectiontype_index'),

    # Network Service Connection Type Details
    path('network_service_connection_types/<slug:slug>/', views.NetworkServiceConnectionTypeDetailView.as_view(), name='networkserviceconnectiontype_detail'),

    # Network Service Connection Index
    path('network_service_connections/', views.NetworkServiceConnectionIndexView.as_view(), name='networkserviceconnection_index'),

    # Network Service Connection Details
    path('network_service_connections/<int:pk>/', views.NetworkServiceConnectionDetailView.as_view(), name='networkserviceconnection_detail'),

    # NIC Index
    path('nics/', views.NICIndexView.as_view(), name='nic_index'),

    # NIC Details
    path('nics/<int:pk>/', views.NICDetailView.as_view(), name='nic_detail'),

    # Routing Type Index
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_index'),

    # Routing Type Details
    path('routing_types/<slug:slug>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),
]
