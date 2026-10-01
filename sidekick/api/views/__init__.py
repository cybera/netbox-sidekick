"""
Sidekick API views.

Every view in this package that subclasses ``rest_framework.views.APIView``
directly must have a docstring. NetBox 4.x builds its API schema with
drf-spectacular, and
``netbox.core.api.schema.NetBoxAutoSchema.get_description()`` falls back to
reading ``self.view.queryset`` for any view that has no docstring. A bare
``APIView`` has no ``queryset``, so one undocumented view breaks the whole
``/api/schema/`` endpoint with
``AttributeError: '<View>' object has no attribute 'queryset'``.

That matters well beyond API documentation. ``netbox.netbox.nb_inventory``
introspects ``/api/schema/`` to discover which query filters exist, so a broken
schema makes every NetBox dynamic inventory fail to parse. See
``sidekick/tests/test_api_schema.py``.
"""

from .accounting import AccountingProfileViewSet               # noqa: F401
from .accounting import AccountingSourceViewSet                # noqa: F401
from .accounting import BandwidthProfileViewSet                # noqa: F401
from .accounting import CurrentBandwidthView                   # noqa: F401
from .accounting import AllCurrentBandwidthView                # noqa: F401
from .clickhousedims import ClickHouseDimsView                 # noqa: F401
from .device import DeviceCheckAccessView                      # noqa: F401
from .networkservice import LogicalSystemViewSet               # noqa: F401
from .networkservice import RoutingTypeViewSet                 # noqa: F401
from .networkservice import NetworkServiceTypeViewSet          # noqa: F401
from .networkservice import NetworkServiceViewSet              # noqa: F401
from .networkservice import NetworkServiceDeviceViewSet        # noqa: F401
from .networkservice import NetworkServiceL2ViewSet            # noqa: F401
from .networkservice import NetworkServiceL3ViewSet            # noqa: F401
from .networkservice import NetworkServiceGroupViewSet         # noqa: F401
from .networkservice import NetworkServiceDuplicateInterfaces  # noqa: F401
from .networkservice import NetworkServiceAdvertisedPrefixes   # noqa: F401
from .networkservice import NetworkServiceFastNetMonData        # noqa: F401
from .networkusage import NetworkUsageListGroupsView           # noqa: F401
from .networkusage import NetworkUsageListMembersView          # noqa: F401
from .networkusage import NetworkUsageGroupView                # noqa: F401
from .networkusage import NetworkUsageMemberView               # noqa: F401
from .nic import NICListView                                   # noqa: F401
