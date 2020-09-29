from napalm.junos.junos import JunOSDriver
from . import junos_views


# SidekickJunOSDriver provides extensions to the base
# NAPALM JunOSDriver.
class SidekickJunOSDriver(JunOSDriver):
    # get_interfaces_counters calls the base get_interfaces_counters
    # method to get a list of interface counters.
    #
    # It then calls the custom junos_logical_iface_counter_table view,
    # found in the local junos_views.yml file, to get the counters for
    # all of the logical interfaces.
    def get_interfaces_counters(self):
        interface_counters = super().get_interfaces_counters()
        query = junos_views.junos_logical_iface_counter_table(self.device)
        query.get()
        for interface, counters in query.items():
            interface_counters[interface] = {
                k: v if v is not None else -1 for k, v in counters
            }
        return interface_counters
