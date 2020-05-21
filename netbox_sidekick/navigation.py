from extras.plugins import PluginMenuItem

menu_items = (
    PluginMenuItem(
        link='plugins:netbox_sidekick:member_index',
        link_text='Members',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:membertype_index',
        link_text='Member Types',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:membernode_index',
        link_text='Member Nodes',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:membernodetype_index',
        link_text='Member Node Types',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:membernodelink_index',
        link_text='Member Node Links',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:membernodelinktype_index',
        link_text='Member Node Link Types',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:networkservice_index',
        link_text='Services',
    ),
    PluginMenuItem(
        link='plugins:netbox_sidekick:networkservicetype_index',
        link_text='Service Types',
    ),
)
