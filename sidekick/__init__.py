from netbox.plugins import PluginConfig


class SidekickConfig(PluginConfig):
    name = "sidekick"
    base_url = "sidekick"
    verbose_name = "Sidekick"
    description = "Additions and changes to Netbox to suit Cybera"
    version = "0.0.1"
    author = "sidekick"
    author_email = "network@cybera.ca"
    required_settings = []
    default_settings = {}


config = SidekickConfig
