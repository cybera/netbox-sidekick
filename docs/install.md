# Installation

## Current development instructions:

1. Have a working [NetBox](https://netbox.readthedocs.io/en/stable/) installation.

2. Clone the `netbox-sidekick` repo somewhere on the NetBox server:

```shell
$ cd /opt
$ git clone https://github.com/cybera/netbox-sidekick
```

3. Install it:

```shell
$ cd netbox-sidekick
$ python setup.py develop
```

4. Follow the Post-Install instructions

## Future stable instructions:

1. Have a working [NetBox](https://netbox.readthedocs.io/en/stable/) installation.

2. Add `netbox-sidekick` to `local_requirements.txt` in the root of the NetBox
installation directory.

3. Install the requirements:

```shell
$ pip install -r local_requirements.txt
```

4. Follow the Post-Install instructions

## Post-Install instructions

1. Modify the NetBox `configuration.py` file to enable the plugin:

```
PLUGINS = [
  'sidekick',
]
```

2. Install the migrations:

```shell
$ cd /opt/netbox/netbox
$ python manage.py migrate sidekick
```

3. Run the setup script:

```shell
$ cd /opt/netbox/netbox
$ python manage.py migrate setup_sidekick
```

4. Restart NetBox:

```shell
$ sudo service netbox restart
$ sudo service netbox-rq restart
```

# Removing

If you are terrified of what you've just installed or it's simply not useful,
you can remove this plugin by:

1. Modify the NetBox `configuration.py` file and remove `sidekick` from
   the list of plugins.

2. You can delete all data from the database by doing:

```
psql netbox
\d
drop table sidekick_nic;
drop table sidekick_networkservicel3;
drop table sidekick_networkservicel2;
drop table sidekick_networkservicedevice;
drop table sidekick_networkservice;
drop table sidekick_logicalsystem;
drop table sidekick_routingtype;
drop table sidekick_networkservicetype;
drop table sidekick_membercontact;
drop table sidekick_contact;
drop table sidekick_contacttype;

delete from django_migrations where app = 'sidekick';
```
