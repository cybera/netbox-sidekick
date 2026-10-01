from django.test import Client, TestCase

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
        self.user = User.objects.create_superuser('testuser')
        self.token = Token.objects.create(user=self.user)
        self.header = {'HTTP_AUTHORIZATION': 'Token {}'.format(self.token.key)}
        self.client = Client()
        self.client.force_login(self.user)
