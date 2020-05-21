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

    # Network Service Type Index
    path('network_service_types/', views.NetworkServiceTypeIndexView.as_view(), name='networkservicetype_index'),

    # Network Service Type Details
    path('network_service_types/<slug:slug>/', views.NetworkServiceTypeDetailView.as_view(), name='networkservicetype_detail'),

    # Network Service Index
    path('network_services/', views.NetworkServiceIndexView.as_view(), name='networkservice_index'),

    # Network Service Details
    path('network_services/<int:pk>/', views.NetworkServiceDetailView.as_view(), name='networkservice_detail'),
]
