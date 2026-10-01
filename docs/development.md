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
   `models` directory, then add an import statement to `models/__init__.py`.
   New or changed models require a migration (see "Update Migrations" below).

2. Define a filter for the model in the `filtersets` directory (a
   `NetBoxModelFilterSet` plus a matching `NetBoxModelFilterSetForm`) and add
   an import statement to `filtersets/__init__.py`. Provide a `search()` method
   so the list view's search box works, and declare `<field>_id` filters for
   foreign keys so related-object tables and panels can link to filtered lists.

3. Define the model's table in the `tables` directory and export it from
   `tables/__init__.py`.

4. Define the model's form(s) in the `forms` directory and export them from
   `forms/__init__.py`.

5. Register the views in `views/` using `@register_model_view` (list, detail,
   add/edit, delete, bulk operations). Detail views should render a
   `SimpleLayout` from `ui/panels.py` rather than a hand-written template, and
   should inherit `SidekickObjectView` so the related-objects panel works.

6. Wire the model's URLs in `urls.py` with `get_model_urls('sidekick',
   '<model_name>')` (list views with `detail=False`, detail views with the
   default `detail=True`).

7. Add navigation entries to the `navigation.py` menu, and (optionally) a
   `SearchIndex` to `search.py`.

8. Inject any additional per-object content (graphs, etc.) via a
   `PluginTemplateExtension` in `template_content/` and register it in
   `template_content/__init__.py`. Note: there is no Django admin integration —
   NetBox 4 removed `django.contrib.admin` (see ADR-064).

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
$ python manage.py test sidekick
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
$ python manage.py makemigrations sidekick
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
$ python manage.py graph_models sidekick > ~/output.dot
$ dot -Tpng ~/output.dot -o /opt/netbox-sidekick/docs/img/models.png
```

> There's a helper script in the `scripts` directory, but it assumes
> certain directory locations.

## Add unit tests where possible

For any changes that you make, if it's possible to create a unit test
for it, please do so.

Unit tests are stored in the `sidekick/tests` directory. Files begin
with `test_`.

To test the files, run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py test sidekick
```

## Reproducing CI Environment Locally

To ensure your changes will pass on GitHub Actions, you can run the tests in a dedicated, isolated environment that mirrors the CI runners.

### CI-Mimic Test Run
Use the specialized Docker Compose file located in `scripts/`:

```bash
# Clean up any previous runs and volumes
docker compose -f scripts/docker-compose.ci.yml down -v

# Run the full suite (installs dependencies, clones NetBox, runs linting + tests)
docker compose -f scripts/docker-compose.ci.yml run --rm ci-runner
```

This environment uses:
- **Python:** 3.12 (Bookworm)
- **PostgreSQL:** 13 (Alpine)
- **Redis:** Alpine

### Key Files
- `scripts/test.sh`: The main entry point for CI testing.
- `scripts/configuration.testing.py`: Base NetBox configuration for tests.
- `scripts/docker-compose.ci.yml`: Docker definition for the CI-mimic environment.
