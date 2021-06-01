from dcim.models import Device

from django.conf import settings
from django.http import Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from napalm import get_network_driver

from netbox.api.authentication import TokenAuthentication

from sidekick.utils import decrypt_secret


class DeviceCheckAccessView(APIView):
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, *args, **kwargs):
        device_id = self.kwargs.get('device', None)
        if device_id is None:
            raise Http404

        # Ensure the device exists.
        try:
            device = Device.objects.get(id=device_id)
        except Device.DoesNotExist:
            raise Http404

        # Ensure the device has been configured with an IP to connect to.
        mgmt_ip = device.primary_ip4
        if mgmt_ip is None:
            raise Http404

        if device.platform is None:
            raise Http404

        # Determine the NAPALM driver to use
        napalm_driver = None
        if device.platform.name == 'Juniper Junos':
            napalm_driver = 'junos'
        if device.platform.name == 'Arista EOS':
            napalm_driver = 'eos'

        # Get the information to decrypt the device's credentials.
        secret_username = settings.PLUGINS_CONFIG['sidekick'].get('secret_user', None)
        private_key_path = settings.PLUGINS_CONFIG['sidekick'].get('secret_private_key_path', None)

        # Ensure we have everything to connect to the device.
        if napalm_driver is None or secret_username is None or private_key_path is None:
            raise Http404

        _mgmt_ip = "%s" % (mgmt_ip.address.ip)

        # Attempt to decrypt the device's credentials.
        try:
            username = decrypt_secret(device, 'username', secret_username, private_key_path)
            password = decrypt_secret(device, 'password', secret_username, private_key_path)
        except Exception:
            raise Http404

        try:
            driver = get_network_driver(napalm_driver)
            napalm_device = driver(_mgmt_ip, username, password, timeout=15)
            napalm_device.open()
            napalm_device.close()
            return Response({'connected': True})
        except Exception:
            return Response({'connected': False})
