from dcim.models import Device

from django.conf import settings
from django.http import Http404

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from napalm import get_network_driver

from netbox.api.authentication import TokenAuthentication

from sidekick.utils import decrypt_1pw_secret


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
        napalm_driver = device.platform.name

        # Get the information to decrypt the device's credentials.
        onepw_host = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_host', None)
        onepw_token_path = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_token_path', None)
        onepw_vault = settings.PLUGINS_CONFIG['sidekick'].get('1pw_connect_readonly_vault', None)

        # Ensure we have everything to connect to the device.
        if napalm_driver is None or onepw_host is None or onepw_token_path is None or onepw_vault is None:
            raise Http404

        _mgmt_ip = "%s" % (mgmt_ip.address.ip)

        # Attempt to decrypt the device's credentials.
        try:
            username = decrypt_1pw_secret(onepw_token_path, onepw_host, onepw_vault, f"{device}", 'username')
            password = decrypt_1pw_secret(onepw_token_path, onepw_host, onepw_vault, f"{device}", 'password')
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
