from django.apps import apps
from django.conf.urls import include
from django.contrib.auth.models import User
from django.test import Client, TestCase
from django.urls import path
from django.utils.module_loading import import_string

from users.models import Token

from netbox.urls import _patterns


class BaseTest(TestCase):
    fixtures = [
        'test-contact.yaml',
        'test-device.yaml',
        'test-member.yaml',
        'test-membernode.yaml',
        'test-networkservice.yaml',
    ]

    def setUp(self):
        # Amend the main netbox urls with this plugin's urls
        # This is a bit of a hack - for some reason the plugin's urls
        # aren't recognized automatically.
        app = apps.get_app_config('netbox_sidekick')
        base_url = getattr(app, 'base_url') or app.label

        urlpatterns = import_string('netbox_sidekick.urls.urlpatterns')
        plugin_patterns = [
            path(f"{base_url}/", include((urlpatterns, app.label)))
        ]

        urlpatterns = import_string('netbox_sidekick.api.urls.urlpatterns')
        plugin_api_patterns = [
            path(f"{base_url}/", include((urlpatterns, f"{app.label}-api")))
        ]

        _patterns.append(path('plugins/', include((plugin_patterns, 'plugins'))))
        _patterns.append(path('api/plugins/', include((plugin_api_patterns, 'plugins-api'))))

        # Setup a test user
        self.user = User.objects.create_superuser('testuser')
        self.token = Token.objects.create(user=self.user)
        self.header = {'HTTP_AUTHORIZATION': 'Token {}'.format(self.token.key)}
        self.client = Client()
        self.client.force_login(self.user)
