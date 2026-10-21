# Global Parallel Network — Cloud-on-Cloud × Edge-on-Edge × Starlink
# origin_signature: MrLiouWord

from .cloud_on_cloud import CloudOnCloud, CloudRegion, CloudTier
from .edge_on_edge import EdgeOnEdge, EdgeNode, EdgeProvider
from .starlink_bridge import StarlinkBridge, SatelliteRelay, OrbitLayer
from .parallel_world_router import ParallelWorldRouter, RouteDecision
from .global_network import GlobalParallelNetwork

__all__ = [
    "GlobalParallelNetwork",
    "CloudOnCloud", "CloudRegion", "CloudTier",
    "EdgeOnEdge", "EdgeNode", "EdgeProvider",
    "StarlinkBridge", "SatelliteRelay", "OrbitLayer",
    "ParallelWorldRouter", "RouteDecision",
]
