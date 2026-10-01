from .interface import InterfaceNICPanel                # noqa: F401
from .networkservice import (                          # noqa: F401
    NetworkServiceGraph,
    NetworkServiceGroupGraph,
)

template_extensions = [
    InterfaceNICPanel,
    NetworkServiceGraph,
    NetworkServiceGroupGraph,
]
