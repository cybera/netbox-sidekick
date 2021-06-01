from django.core.management.base import BaseCommand

from sidekick.utils.gren_map import generate_map


class Command(BaseCommand):
    help = "Generate GREN XML Map"

    def handle(self, *args, **options):
        g = generate_map()

        self.stdout.write("Institutions:")
        for v in g.get_institutions():
            self.stdout.write(f"  - {v.name}")

        self.stdout.write("Links:")
        for v in g.get_links():
            self.stdout.write(f"  - {v.name}")

        self.stdout.write("Nodes:")
        for v in g.get_nodes():
            self.stdout.write(f"  - {v.name}")
