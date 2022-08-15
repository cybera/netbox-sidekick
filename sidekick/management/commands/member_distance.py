import geopy.distance

from django.core.management.base import BaseCommand

from sidekick.utils.gren_map import generate_map


class Command(BaseCommand):
    help = "Calculate distance of members"

    def handle(self, *args, **options):
        total_distance = 0

        g = generate_map()
        for v in g.get_links():
            nodes = []
            for node in v.nodes:
                nodes.append(node)

            node_a = nodes[0]
            node_z = nodes[1]

            node_a_coord = (node_a.latitude, node_a.longitude)
            node_z_coord = (node_z.latitude, node_z.longitude)

            dist = geopy.distance.distance(node_a_coord, node_z_coord).km
            total_distance += dist
            print(f"{node_a.name} {node_a_coord} => {node_z.name} {node_z_coord}:", dist)

        print(total_distance)
