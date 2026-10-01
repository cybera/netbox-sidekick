from django.test import Client, TestCase

from users.constants import TOKEN_PREFIX
from users.models import Token, User


class BaseTest(TestCase):
    fixtures = [
        'test-accounting.yaml',
        'test-customfield.yaml',
        'test-device.yaml',
        'test-ipam.yaml',
        'test-networkservice.yaml',
        'test-nic.yaml',
        'test-tenant.yaml',
    ]

    def setUp(self):
        # Create a superuser and a token for API requests. Plugin URL patterns
        # are registered automatically by NetBox (netbox.plugins.urls), so no
        # manual URL wiring is required here.
        #
        # NetBox 4.x creates v2 tokens by default, which are presented as
        # ``Bearer nbt_<key>.<token>`` (see netbox/api/authentication.py). The
        # legacy v1 scheme (``Token <token>``) is rejected with
        # "Invalid v1 token".
        self.user = User.objects.create_superuser('testuser')
        self.token = Token.objects.create(user=self.user)
        self.header = {
            'HTTP_AUTHORIZATION': f'Bearer {TOKEN_PREFIX}{self.token.key}.{self.token.token}'
        }
        self.client = Client()
        self.client.force_login(self.user)
