import grenml

from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from netbox_sidekick.api.renderers.plaintext import PlainTextRenderer
from netbox_sidekick.models import MemberNodeLink


class FullMapViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    renderer_classes = (PlainTextRenderer,)

    def list(self, request):
        grenml_manager = grenml.GRENMLManager('Cybera')

        # This builds a map by searching for all links,
        # and then walking backwards from the link, node, and owner/institution.
        for link in MemberNodeLink.objects.all():
            node_ids = []
            for node in (link.a_endpoint, link.z_endpoint):
                # Add the Institution of the link
                owner = node.owner
                try:
                    institution_id = grenml_manager.get_institution(name=owner.tenant.description)
                except grenml.exceptions.InstitutionNotFoundError:
                    primary_owner = False
                    if owner.tenant.description == 'Cybera':
                        primary_owner = True

                    address = owner.billing_address_1
                    if owner.billing_address_2 != "":
                        address = f"{owner.billing_address_1}, {owner.billing_address_2}"
                    address = f"{address}, {owner.billing_city}, {owner.billing_postal_code}, {owner.billing_province}, {owner.billing_country}"

                    member_type = owner.member_type.name.lower()
                    if member_type not in grenml.models.institutions.INSTITUTION_TYPES:
                        member_type = 'connected institution'

                    institution_id = grenml_manager.add_institution(
                        name=owner.tenant.description,
                        primary_owner=primary_owner,
                        address=address,
                        institution_type=member_type,
                        longitude=owner.longitude,
                        latitude=owner.latitude,
                    )

                # Add the nodes of the link
                try:
                    grenml_manager.get_node(name=node.name)
                except grenml.exceptions.NodeNotFoundError:
                    grenml_manager.add_node(
                        name=node.name,
                        short_name=node.label,
                        longitude=node.longitude,
                        latitude=node.latitude,
                        altitude=node.altitude,
                        address=node.address,
                        owners=[institution_id],
                    )

            # Add the links
            # Get the institution ID of the owner.
            institution_id = grenml_manager.get_institution(name=link.owner.tenant.description)

            # Get the node IDs.
            node_ids = []
            for node in (link.a_endpoint, link.z_endpoint):
                node_id = grenml_manager.get_node(name=node.name)
                node_ids.append(node_id)

            try:
                grenml_manager.get_link(name=link.name)
            except grenml.exceptions.LinkNotFoundError:
                grenml_manager.add_link(
                    name=link.name,
                    short_name=link.label,
                    owners=[institution_id],
                    nodes=node_ids,
                )

        output_string = grenml_manager.write_to_string()
        return Response(output_string)
