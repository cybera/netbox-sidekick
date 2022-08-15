import grenml

from django.conf import settings
from django.db.models import Q
from django.utils.text import slugify

from dcim.models import (
    Site
)

from sidekick.models import (
    NetworkService
)


def generate_map():
    # Get the name of the primary owner of the map.
    # If one isn't found, stop early.
    owner_name = settings.PLUGINS_CONFIG['sidekick'].get('mapping_primary_owner', None)
    if owner_name is None:
        return

    grenml_manager = grenml.GRENMLManager(owner_name)

    primary_site_name = settings.PLUGINS_CONFIG['sidekick'].get('mapping_primary_site', None)
    if primary_site_name is None:
        raise("mapping_primary_site is not defined in netbox config")

    # First build the information for the primary owner.
    primary_site = Site.objects.filter(
        Q(name=primary_site_name) | Q(description=primary_site_name))
    if len(primary_site) != 1:
        raise(f"Could not find a single primary site titled {primary_site_name}")

    primary_site = primary_site[0]
    primary_site_name = primary_site.name
    if primary_site.description is not None and primary_site.description != "":
        primary_site_name = primary_site.description

    owner_id = slugify(f"{owner_name}-{primary_site_name}")[:128]
    grenml_manager.add_institution(
        id=owner_id,
        name=owner_name,
        primary_owner=True,
        institution_type='RREN',
        latitude=primary_site.latitude,
        longitude=primary_site.longitude,
    )

    grenml_manager.add_node(
        id=owner_id,
        name=primary_site_name,
        latitude=primary_site.latitude,
        longitude=primary_site.longitude,
        owners=[owner_id],
    )

    # Loop through all network services that have a defined Member Site.
    services = NetworkService.objects.filter(~Q(member_site=None))
    for service in services:
        devices = service.network_service_devices.all()

        # A device is a core router of the NREN that the member connects to.
        # Don't continue if the service doesn't have any devices.
        if len(devices) == 0:
            continue

        device = devices[0].device
        nren_site_name = device.site.name
        if device.site.description is not None and device.site.description != "":
            nren_site_name = device.site.description

        if device.site.latitude is None or device.site.latitude == "":
            continue

        if device.site.longitude is None or device.site.longitude == "":
            continue

        nren_node_id = slugify(f"{owner_name}-{nren_site_name}")[:128]
        try:
            grenml_manager.get_node(id=nren_node_id)
        except grenml.exceptions.NodeNotFoundError:
            grenml_manager.add_node(
                id=nren_node_id,
                name=nren_site_name,
                latitude=device.site.latitude,
                longitude=device.site.longitude,
                owners=[owner_id],
            )

            # Create a link between the nren site and primary location
            link_name = f"{primary_site_name} to {nren_site_name}"
            link_id = slugify(f"{owner_name}-{link_name}")[:128]

            try:
                grenml_manager.get_link(id=link_id)
            except grenml.exceptions.LinkNotFoundError:
                grenml_manager.add_link(
                    name=link_name,
                    owners=[owner_id],
                    nodes=[nren_node_id, owner_id],
                )

        # Each member service links to a member site, such as their main office.
        member_site = service.member_site
        member = service.member

        lat = member_site.latitude
        if lat is None or lat == "":
            continue

        lon = member_site.longitude
        if lon is None or lon == "":
            continue

        member_id = slugify(f"{owner_name}-{member.name}")[:128]

        try:
            grenml_manager.get_institution(id=member_id)
        except grenml.exceptions.InstitutionNotFoundError:
            member_type = 'connected institution'
            if 'member_type' in member.cf:
                member_type = member.cf['member_type']

                # Add the member to the map.
                grenml_manager.add_institution(
                    id=member_id,
                    name=member.name,
                    primary_owner=False,
                    institution_type=member_type,
                    latitude=lat,
                    longitude=lon,
                )

                # Add the member's service, as a node, to the map using the same location.
                # This limits one node per member and should be expanded in the future.
                try:
                    grenml_manager.get_node(id=member_id)
                except grenml.exceptions.NodeNotFoundError:
                    grenml_manager.add_node(
                        id=member_id,
                        name=member.name,
                        latitude=lat,
                        longitude=lon,
                        owners=[member_id],
                    )

                # Add a link between the member and device.
                link_name = f"{nren_site_name} to {member.name}"
                link_id = slugify(f"{owner_name}-{link_name}")[:128]
                try:
                    grenml_manager.get_link(id=link_id)
                except grenml.exceptions.LinkNotFoundError:
                    grenml_manager.add_link(
                        id=link_id,
                        name=link_name,
                        owners=[owner_id, member_id],
                        nodes=[member_id, nren_node_id],
                    )

    return grenml_manager
