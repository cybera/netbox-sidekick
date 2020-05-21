from extras.plugins import PluginConfig


class NetboxsidekickConfig(PluginConfig):
    name = "netbox_sidekick"
    base_url = "sidekick"
    verbose_name = "sidekick Additions for Netbox"
    description = "Additions and changes to Netbox to suit sidekick"
    version = "0.0.1"
    author = "sidekick"
    author_email = "network@sidekick.ca"
    required_settings = []
    default_settings = {}


config = NetboxsidekickConfig
