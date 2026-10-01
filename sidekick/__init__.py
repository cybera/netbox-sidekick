from netbox.plugins import PluginConfig


class SidekickConfig(PluginConfig):
    name = "sidekick"
    base_url = "sidekick"
    verbose_name = "Sidekick"
    description = "Additions and changes to NetBox to suit Cybera"
    version = "0.0.1"
    author = "sidekick"
    author_email = "network@cybera.ca"
    min_version = "4.0"
    max_version = "4.7"
    required_settings = []
    default_settings = {
        # Traffic graph backend selection. When False (default), sidekick falls
        # back to Graphite.
        'use_clickhouse': False,
        # ClickHouse connection
        'clickhouse_url': None,
        'clickhouse_database': 'pmacct',
        'clickhouse_user': 'default',
        'clickhouse_password': '',
        'clickhouse_table': None,
        'clickhouse_legacy_table': None,
        'clickhouse_labels_table': None,
        # Graphite (legacy) endpoints
        'graphite_host': None,
        'graphite_render_host': None,
        # 1Password Connect (SNMP credential retrieval)
        '1pw_connect_host': None,
        '1pw_connect_token_path': None,
        '1pw_connect_readonly_vault': None,
        # Legacy import mappings
        'mapping_primary_owner': None,
        'mapping_primary_site': None,
    }


config = SidekickConfig
