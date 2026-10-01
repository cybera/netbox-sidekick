from netbox.plugins import PluginMenu, PluginMenuItem

menu = PluginMenu(
    label='Sidekick',
    groups=(
        ('Services', (
            PluginMenuItem(
                link='plugins:sidekick:networkservice_list',
                link_text='Network Services',
            ),
            PluginMenuItem(
                link='plugins:sidekick:networkservicegroup_list',
                link_text='Network Service Groups',
            ),
            PluginMenuItem(
                link='plugins:sidekick:networkservicetype_list',
                link_text='Service Types',
            ),
            PluginMenuItem(
                link='plugins:sidekick:logicalsystem_list',
                link_text='Logical Systems',
            ),
            PluginMenuItem(
                link='plugins:sidekick:routingtype_list',
                link_text='Routing Types',
            ),
            PluginMenuItem(
                link='plugins:sidekick:peeringconnection_list',
                link_text='Peering Connections',
            ),
        )),
        ('Accounting', (
            PluginMenuItem(
                link='plugins:sidekick:accountingprofile_list',
                link_text='Accounting Profiles',
            ),
            PluginMenuItem(
                link='plugins:sidekick:accountingsource_list',
                link_text='Accounting Sources',
            ),
            PluginMenuItem(
                link='plugins:sidekick:bandwidthprofile_list',
                link_text='Bandwidth Profiles',
            ),
        )),
        ('Interfaces', (
            PluginMenuItem(
                link='plugins:sidekick:nic_list',
                link_text='Interfaces',
            ),
        )),
        ('Members', (
            PluginMenuItem(
                link='plugins:sidekick:memberbandwidth_index',
                link_text='Bandwidth Usage Report',
            ),
            PluginMenuItem(
                link='plugins:sidekick:membercontact_list',
                link_text='Contacts',
            ),
        )),
    ),
    icon_class='mdi mdi-puzzle',
)
