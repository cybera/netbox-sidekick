# Installation

`netbox-sidekick` targets **NetBox 4.0 – 4.7** on **Python 3.12+**.

## Installation

1. Have a working [NetBox](https://netbox.readthedocs.io/en/stable/) 4.x
   installation.

2. Add the plugin to NetBox's `local_requirements.txt`:

   ```
   git+https://github.com/cybera/netbox-sidekick
   ```

3. Install the requirements:

   ```shell
   $ pip install -r local_requirements.txt
   ```

4. Follow the Post-Install instructions below.

## Post-Install

1. Enable the plugin in NetBox's `configuration.py`:

   ```python
   PLUGINS = [
       'sidekick',
   ]
   ```

   Configuration options (all optional) are passed via `PLUGINS_CONFIG`, for
   example:

   ```python
   PLUGINS_CONFIG = {
       'sidekick': {
           # Traffic graph backend. When False (the default), sidekick falls
           # back to Graphite.
           'use_clickhouse': True,
           'clickhouse_url': 'http://clickhouse.example:8123',
           'clickhouse_database': 'pmacct',
           'clickhouse_user': 'default',
           'clickhouse_password': '',
           # Legacy Graphite endpoints (used when use_clickhouse is False)
           'graphite_host': None,
           'graphite_render_host': None,
           # 1Password Connect (SNMP credential retrieval)
           '1pw_connect_host': None,
           '1pw_connect_token_path': None,
           '1pw_connect_readonly_vault': None,
       },
   }
   ```

2. Install the migrations:

   ```shell
   $ cd /opt/netbox/netbox
   $ python manage.py migrate sidekick
   ```

3. Restart NetBox:

   ```shell
   $ sudo systemctl restart netbox netbox-rq
   ```

## Removing

1. Remove `sidekick` from `PLUGINS` in `configuration.py` and restart NetBox.

2. To delete the plugin's data, drop its tables from the NetBox database and
   remove its migration records:

   ```sql
   DROP TABLE sidekick_nic;
   DROP TABLE sidekick_networkservicel3;
   DROP TABLE sidekick_networkservicel2;
   DROP TABLE sidekick_networkservicedevice;
   DROP TABLE sidekick_networkservice;
   DROP TABLE sidekick_networkservicegroup_network_services;
   DROP TABLE sidekick_networkservicegroup;
   DROP TABLE sidekick_accountingsourcecounter;
   DROP TABLE sidekick_accountingsource;
   DROP TABLE sidekick_accountingprofile_accounting_sources;
   DROP TABLE sidekick_accountingprofile;
   DROP TABLE sidekick_bandwidthprofile;
   DROP TABLE sidekick_logicalsystem;
   DROP TABLE sidekick_routingtype;
   DROP TABLE sidekick_networkservicetype;

   DELETE FROM django_migrations WHERE app = 'sidekick';
   ```

   > **Warning:** this permanently deletes sidekick data. Take a database backup
   > first, and confirm the table names against `\dt sidekick_*` before running.
