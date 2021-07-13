from django.core.management.base import BaseCommand

from sidekick.models import (
    AccountingProfile,
)


class Command(BaseCommand):
    help = "Report member bandwidth usage"

    def handle(self, *args, **options):
        # For each Accounting Profile...
        for ap in AccountingProfile.objects.filter(enabled=True):
            # Obtain the current Bandwidth Profile
            bp = ap.get_current_bandwidth_profile()
            if bp is not None:
                # Convert the traffic cap to bytes
                traffic_cap = bp.traffic_cap

                # For each accounting source...
                for accounting_source in ap.accounting_sources.all():
                    # Calculate the current transfer rate
                    current_rate = accounting_source.get_current_rate()

                    # Report if the member is within 10% of their limit.
                    v = float(traffic_cap) - (float(traffic_cap) * 0.10)
                    scu = (current_rate['scu'] * 8) / 1000 / 1000
                    dcu = (current_rate['dcu'] * 8) / 1000 / 1000
                    if scu >= v or dcu >= v:
                        self.stdout.write(f"{ap.member.name}: Cap: {bp.traffic_cap} Current: {scu}/{dcu}")
