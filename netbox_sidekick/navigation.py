from extras.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_sidekick:contact_index',
        link_text='Contacts',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:contacttype_index',
        link_text='Contact Types',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:logicalsystem_index',
        link_text='Logical Systems',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:nic_index',
        link_text='NICs',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:routingtype_index',
        link_text='Routing Types',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:networkserviceconnection_index',
        link_text='Service Connections',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:networkserviceconnectiontype_index',
        link_text='Service Connection Types',
    ),
)
