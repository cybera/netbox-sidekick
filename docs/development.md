# Development Guidelines

## Use Flake8

Use [Flake8](https://flake8.pycqa.org/en/latest/) for a standard code style.
At the moment, we're ignoring W504 and E501. We're not monsters.

For `vim` and Syntastic:

```
let g:syntastic_python_checkers = ['flake8']
let g:syntastic_python_flake8_post_args='--ignore=W504,E501'
```

## Working With Models

### Creating Models

If you need to create a model, please use the following process:

1. Define the model in either a new or an existing related file under the
   `models` directory.

2. Once created, add an import statement to the `models/__init__.py` file.

3. Add an admin entry for the model to the `admin.py` file.

4. Define a filter for the model in the `filters` directory. Either add the
   filter to a new or an existing related file. Also add an import statement
   to the `filters/__init__.py` file.

4. Repeat the process for `tables` and `views`.

5. Define at least two standard templates for indexing and detail views in the
   `templates/netbox_sidekick` directory.

8. Add new URLs to the `urls.py` fiile.

7. Add navigation entries to the `navigation.py` file.

Once this is in place, add some basic unit tests to ensure basic functionality
works:

1. Create any required fixtures under the `fixtures` directory. If you define
   fixtures in a new file, add a reference to that file in the
   `tests/utils.py` file.

2. Create some basic unit tests, using existing tests as references, to either
   a new or an existing related file in the `tests` directory.

Run the suite of tests by doing:

```shell
$ cd /opt/netbox/netbox
$ python manage.py test netbox_sidekick
```

### Update Migrations

If you add new models or modify existing mdoels, you will need to generate a new
set of migrations.

First make sure you have the following in `configuration.py`:

```
DEVELOPER = True
```

Then run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py makemigrations netbox_sidekick
```

### Generate a Model Diagram

If you make any changes to `models.py`, please make sure to update the model
diagram located at `docs/img/models.png`:

First, install some dependencies:

```
$ sudo apt-get install -y graphviz
$ pip install django-extensions
$ pip install graphviz
```

Next, add `django_extensions` to the list of `INSTALLED_APPS` in
`netbox/netbox/settings.py`:

```
INSTALLED_APPS = [
    ...
    'django_extensions',
    ...
]
```

Then generate the image:

```
$ cd /opt/netbox/netbox
$ python manage.py graph_models netbox_sidekick > ~/output.dot
$ dot -Tpng ~/output.dot -o /opt/netbox-sidekick/docs/img/models.png
```

> There's a helper script in the `scripts` directory, but it assumes
> certain directory locations.

## Add unit tests where possible

For any changes that you make, if it's possible to create a unit test
for it, please do so.

Unit tests are stored in the `netbox_sidekick/tests` directory. Files begin
with `test_`.

To test the files, run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py test netbox_sidekick
```
