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

    # Member Type Index
    path('member_types/', views.MemberTypeIndexView.as_view(), name='membertype_index'),

    # Member Type Details
    path('member_types/<slug:slug>/', views.MemberTypeDetailView.as_view(), name='membertype_detail'),

    # Member Index
    path('members/', views.MemberIndexView.as_view(), name='member_index'),

    # Member Details
    path('members/<int:pk>/', views.MemberDetailView.as_view(), name='member_detail'),

    # Member Node Type Index
    path('member_node_types/', views.MemberNodeTypeIndexView.as_view(), name='membernodetype_index'),

    # Member Node Type Details
    path('member_node_types/<slug:slug>/', views.MemberNodeTypeDetailView.as_view(), name='membernodetype_detail'),

    # Member Node Index
    path('member_nodes/', views.MemberNodeIndexView.as_view(), name='membernode_index'),

    # Member Node Details
    path('member_nodes/<int:pk>/', views.MemberNodeDetailView.as_view(), name='membernode_detail'),

    # Member Node Link Type Index
    path('member_node_link_types/', views.MemberNodeLinkTypeIndexView.as_view(), name='membernodelinktype_index'),

    # Member Node Type Link Details
    path('member_node_link_types/<slug:slug>/', views.MemberNodeLinkTypeDetailView.as_view(), name='membernodelinktype_detail'),

    # Member Node Link Index
    path('member_node_links/', views.MemberNodeLinkIndexView.as_view(), name='membernodelink_index'),

    # Member Node Link Details
    path('member_node_links/<int:pk>/', views.MemberNodeLinkDetailView.as_view(), name='membernodelink_detail'),

    # Network Service Connection Type Index
    path('network_service_connection_types/', views.NetworkServiceConnectionTypeIndexView.as_view(), name='networkserviceconnectiontype_index'),

    # Network Service Connection Type Details
    path('network_service_connection_types/<slug:slug>/', views.NetworkServiceConnectionTypeDetailView.as_view(), name='networkserviceconnectiontype_detail'),

    # Network Service Connection Index
    path('network_service_connections/', views.NetworkServiceConnectionIndexView.as_view(), name='networkserviceconnection_index'),

    # Network Service Connection Details
    path('network_service_connections/<int:pk>/', views.NetworkServiceConnectionDetailView.as_view(), name='networkserviceconnection_detail'),

    # Routing Type Index
    path('routing_types/', views.RoutingTypeIndexView.as_view(), name='routingtype_index'),

    # Routing Type Details
    path('routing_types/<slug:slug>/', views.RoutingTypeDetailView.as_view(), name='routingtype_detail'),
]
