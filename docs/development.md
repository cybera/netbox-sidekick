# Development Guidelines

## Use Flake8

Use [Flake8](https://flake8.pycqa.org/en/latest/) for a standard code style.
At the moment, we're ignoring W504 and E501. We're not monsters.

For `vim` and Syntastic:

```
let g:syntastic_python_checkers = ['flake8']
let g:syntastic_python_flake8_post_args='--ignore=W504,E501'
```

## Add unit tests where possible

Unit tests are stored in the `netbox_sidekick/tests` directory. Files begin
with `test_`.

To test the files, run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py test netbox_sidekick
```

## Update migrations when required

If you make any changes to `models.py`, you will need to generate a new set of
migrations.

First make sure you have the following in `configuration.py`:

```
DEVELOPER = True
```

Then run:

```shell
$ cd /opt/netbox/netbox
$ python manage.py makemigrations netbox_sidekick
```

## Generate a Model Diagram

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
$ python manage.py graph_models netbox_sidekick > ~/output.png
$ dot -Tpng ~/output.dot -o /opt/netbox-sidekick/docs/img/models.png
```

> There's a helper script in the `scripts` directory, but it assumes
> certain directory locations.
