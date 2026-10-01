from netbox.search import SearchIndex

from sidekick.models import (
    AccountingProfile,
    AccountingSource,
    BandwidthProfile,
    LogicalSystem,
    NetworkService,
    NetworkServiceDevice,
    NetworkServiceGroup,
    NetworkServiceL2,
    NetworkServiceL3,
    NetworkServiceType,
    RoutingType,
)


class LogicalSystemIndex(SearchIndex):
    model = LogicalSystem
    fields = (
        ('name', 100),
        ('slug', 110),
    )


class RoutingTypeIndex(SearchIndex):
    model = RoutingType
    fields = (
        ('name', 100),
        ('slug', 110),
    )


class NetworkServiceTypeIndex(SearchIndex):
    model = NetworkServiceType
    fields = (
        ('name', 100),
        ('slug', 110),
        ('description', 200),
    )


class NetworkServiceIndex(SearchIndex):
    model = NetworkService
    fields = (
        ('name', 100),
        ('description', 200),
        ('legacy_id', 300),
    )
    display_attrs = ('member', 'network_service_type')


class NetworkServiceDeviceIndex(SearchIndex):
    model = NetworkServiceDevice
    fields = (
        ('interface', 100),
        ('legacy_id', 300),
    )
    display_attrs = ('network_service', 'device')


class NetworkServiceL2Index(SearchIndex):
    model = NetworkServiceL2
    fields = (
        ('legacy_id', 300),
    )
    display_attrs = ('network_service_device',)


class NetworkServiceL3Index(SearchIndex):
    model = NetworkServiceL3
    fields = (
        ('legacy_id', 300),
    )
    display_attrs = ('member', 'network_service_device')


class NetworkServiceGroupIndex(SearchIndex):
    model = NetworkServiceGroup
    fields = (
        ('name', 100),
        ('slug', 110),
        ('description', 200),
    )


class AccountingSourceIndex(SearchIndex):
    model = AccountingSource
    fields = (
        ('name', 100),
        ('destination', 200),
    )
    display_attrs = ('device',)


class AccountingProfileIndex(SearchIndex):
    model = AccountingProfile
    fields = (
        ('name', 100),
    )
    display_attrs = ('member',)


class BandwidthProfileIndex(SearchIndex):
    model = BandwidthProfile
    fields = ()
    display_attrs = ('accounting_profile',)


indexes = [
    LogicalSystemIndex,
    RoutingTypeIndex,
    NetworkServiceTypeIndex,
    NetworkServiceIndex,
    NetworkServiceDeviceIndex,
    NetworkServiceL2Index,
    NetworkServiceL3Index,
    NetworkServiceGroupIndex,
    AccountingSourceIndex,
    AccountingProfileIndex,
    BandwidthProfileIndex,
]
