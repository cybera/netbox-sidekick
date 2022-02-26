from sidekick.forms import MemberCreateForm

from sidekick.models import (
    NetworkService,
)

from .utils import BaseTest

initial_form_data = {
    'member_name': 'South University',
    'member_type': 'Post-Secondary Institution',
    'latitude': '0',
    'longitude': '0',
    'network_service_name': 'South University - Primary',
    'network_service_type': 1,
    'start_date': '2022-01-01',
    'device': 1,
    'interface': 'xe-3/3/5.301',
    'vlan': '301',
    'logical_system': 2,
    'routing_type': 1,
    'asn': 7,
    'ipv4_unicast': 1,
    'ipv4_multicast': 1,
    'provider_router_address_ipv4': '192.168.30.1',
    'member_router_address_ipv4': '192.168.30.2',
    'provider_router_address_ipv6': '',
    'member_router_address_ipv6': '',
    'ipv6_unicast': 0,
    'ipv6_multicast': 0,
    'ipv4_prefixes': '192.168.30.0/24',
    'ipv6_prefixes': "",
}


class MemberCreateTest(BaseTest):
    def test_member_create_valid(self):
        form_data = initial_form_data.copy()
        form = MemberCreateForm(data=form_data)
        is_valid = form.is_valid()
        self.assertTrue(is_valid)
        self.assertTrue(form.create_member())

        network_service = NetworkService.objects.get(name="South University - Primary")
        self.assertTrue(network_service.member.name, "South University")
        ipv4_prefixes = network_service.get_ipv4_prefixes()
        self.assertEquals(f"{ipv4_prefixes[0]}", form_data["ipv4_prefixes"])

    def test_member_create_invalid(self):
        form_data = initial_form_data.copy()
        form_data['member_name'] = 'East University'
        form_data['interface'] = 'xe-3/3/6.301',
        form = MemberCreateForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertTrue("Member already exists" in form.errors["member_name"])
        self.assertTrue("A site with the same name already exists" in f"{form.errors['member_name']}")
        self.assertTrue("Interface does not exist on the device" in f"{form.errors['interface']}")
