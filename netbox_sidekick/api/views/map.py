import grenml

from django.conf import settings

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from dcim.models import Device
from tenancy.models import Tenant, TenantGroup

from netbox_sidekick.api.renderers.plaintext import PlainTextRenderer


class FullMapViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = (PlainTextRenderer,)

    def list(self, request):
        # Get the name of the primary owner of the map.
        # If one isn't found, stop early.
        primary_owner_name = settings.PLUGINS_CONFIG['netbox_sidekick'].get('mapping_primary_owner', None)
        if primary_owner_name is None:
            return

        grenml_manager = grenml.GRENMLManager(primary_owner_name)
        nodes = {}

        # First build the information for the primary owner.
        owner = Tenant.objects.get(name=primary_owner_name)

        # If the primary owner doesn't have the latitude and longitude set,
        # skip everything entirely.
        if 'latitude' not in owner.cf or 'longitude' not in owner.cf:
            return

        owner_id = grenml_manager.add_institution(
            name=owner.name,
            primary_owner=True,
            institution_type='RREN',
            latitude=owner.cf['latitude'],
            longitude=owner.cf['longitude'],
        )

        # Find all devices owned by the owner and add them as nodes.
        devices = Device.objects.filter(tenant__group__name=primary_owner_name)
        primary_node = None
        for device in devices:
            # Only devices that have a latitude and longitude set will
            # be added as nodes.
            if 'latitude' not in device.cf or 'longitude' not in device.cf:
                continue

            device_lat = device.cf['latitude']
            device_lon = device.cf['longitude']

            map_label = device.name
            if 'map_label' in device.cf:
                map_label = device.cf['map_label']

            node_id = grenml_manager.add_node(
                name=map_label,
                latitude=device_lat,
                longitude=device_lon,
                owners=[owner_id],
            )
            nodes[device.id] = node_id

            if 'primary_map_node' in device.cf and device.cf['primary_map_node'] is True:
                primary_node = device

        # Create links between all devices and the primary node.
        if primary_node is not None:
            for device in devices:
                # Only devices that have a latitude and longitude set will
                # be added as nodes.
                if 'latitude' not in device.cf or 'longitude' not in device.cf:
                    continue

                if device.id != primary_node.id:
                    map_label = f"{primary_node.name} to {device.name}"
                    if 'map_label' in device.cf and 'map_label' in primary_node.cf:
                        map_label = f"{primary_node.cf['map_label']} to {device.cf['map_label']}"

                    grenml_manager.add_link(
                        name=map_label,
                        owners=[owner_id],
                        nodes=[nodes[device.id], nodes[primary_node.id]],
                    )

        # With the owner mapped, now map all members.
        members = TenantGroup.objects.get(name="Members")
        for member in members.tenants.all():
            if 'latitude' not in member.cf or 'longitude' not in member.cf:
                continue

            member_lat = member.cf['latitude']
            member_lon = member.cf['longitude']
            if member_lat == "" or member_lon == "":
                continue

            services = member.networkservice_set.all()

            if len(services) == 0:
                continue

            # Currently, we're only mapping one member location.
            # This might be a little buggy if a member has services
            # at multiple PoPs and their home address doesn't match.
            service = services[0]

            devices = service.network_service_devices.all()
            if len(devices) == 0:
                continue

            device = devices[0].device
            if device.id not in nodes.keys():
                continue

            device_lat = device.cf['latitude']
            device_lon = device.cf['longitude']

            try:
                inst_id = grenml_manager.get_institution(name=member.name)
            except grenml.exceptions.InstitutionNotFoundError:
                member_type = 'connected institution'
                if 'member_type' in member.cf:
                    member_type = member.cf['member_type']

                    # Add the member to the map.
                    inst_id = grenml_manager.add_institution(
                        name=member.name,
                        primary_owner=False,
                        institution_type=member_type,
                        latitude=member_lat,
                        longitude=member_lon,
                    )

                    # Add the member's service to the map.
                    # Using the same location.
                    try:
                        node_id = grenml_manager.get_node(name=member.name)
                    except grenml.exceptions.NodeNotFoundError:
                        node_id = grenml_manager.add_node(
                            name=member.name,
                            latitude=member_lat,
                            longitude=member_lon,
                            owners=[inst_id],
                        )

                    # Add a link between the member and device.
                    map_label = f"{device.name} to {member.name}"
                    if 'map_label' in device.cf:
                        map_label = f"{device.cf['map_label']} to {member.name}"

                    grenml_manager.add_link(
                        name=map_label,
                        owners=[inst_id],
                        nodes=[nodes[device.id], node_id],
                    )

        output_string = grenml_manager.write_to_string()
        return Response(output_string)
