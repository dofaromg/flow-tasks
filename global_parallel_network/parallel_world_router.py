"""
Parallel World Router (平行世界路由器)
origin_signature: MrLiouWord

Unified routing across all three network planes:
  - Cloud-on-Cloud (L0-L1)
  - Edge-on-Edge (L2-L3)
  - Starlink Bridge (L-1 physical)

Implements the MRLiou layer model routing:
  L-1  Physical (satellite, hardware)
  L0   Cloud infrastructure
  L1   Meta-Cloud (cloud-on-cloud)
  L2   Edge nodes
  L3   Meta-Edge (edge-on-edge)
  L4   Application services
  L5   Cognitive / AI
  L6   ASI decision
  L7   World state (Ω)

A request enters at any layer and the router decides the optimal
cross-plane path based on latency, cost, and reliability.
"""

import time
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional


class NetworkPlane(Enum):
    SATELLITE = "satellite"   # L-1
    CLOUD = "cloud"           # L0-L1
    EDGE = "edge"             # L2-L3


class LayerID(Enum):
    L_NEG1 = "L-1"
    L0 = "L0"
    L1 = "L1"
    L2 = "L2"
    L3 = "L3"
    L4 = "L4"
    L5 = "L5"
    L6 = "L6"
    L7 = "L7"


@dataclass
class RouteDecision:
    """Result of a routing decision."""
    request_id: str
    source_plane: NetworkPlane
    target_plane: NetworkPlane
    source_layer: LayerID
    target_layer: LayerID
    selected_path: List[str]
    estimated_latency_ms: float
    estimated_cost: float
    reliability: float
    reason: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class CrossPlaneLink:
    """A link connecting two different network planes."""
    source_plane: NetworkPlane
    source_node: str
    target_plane: NetworkPlane
    target_node: str
    latency_ms: float
    bandwidth_gbps: float
    cost_per_gb: float = 0.0
    is_active: bool = True


class ParallelWorldRouter:
    """
    Routes requests across satellite, cloud, and edge planes.

    The router maintains cross-plane links (e.g., ground-station → cloud-region,
    edge-pop → cloud-region, ground-station → edge-pop) and selects the optimal
    path based on the request's QoS requirements.
    """

    def __init__(self):
        self.cross_links: List[CrossPlaneLink] = []
        self.decisions: List[RouteDecision] = []
        self.layer_map: Dict[LayerID, NetworkPlane] = {
            LayerID.L_NEG1: NetworkPlane.SATELLITE,
            LayerID.L0: NetworkPlane.CLOUD,
            LayerID.L1: NetworkPlane.CLOUD,
            LayerID.L2: NetworkPlane.EDGE,
            LayerID.L3: NetworkPlane.EDGE,
            LayerID.L4: NetworkPlane.CLOUD,  # app services run on cloud
            LayerID.L5: NetworkPlane.CLOUD,  # AI on cloud GPU
            LayerID.L6: NetworkPlane.CLOUD,  # ASI on cloud
            LayerID.L7: NetworkPlane.CLOUD,  # world state on cloud
        }
        self.origin_signature = "MrLiouWord"
        self._init_default_cross_links()

    def _init_default_cross_links(self):
        """Bootstrap cross-plane links."""
        defaults = [
            # Ground station → Cloud region
            (NetworkPlane.SATELLITE, "gs-tw", NetworkPlane.CLOUD, "gcp-asia-east1", 5.0, 10.0, 0.01),
            (NetworkPlane.SATELLITE, "gs-us-west", NetworkPlane.CLOUD, "aws-us-east-1", 15.0, 25.0, 0.01),
            (NetworkPlane.SATELLITE, "gs-us-east", NetworkPlane.CLOUD, "aws-us-east-1", 3.0, 25.0, 0.01),
            (NetworkPlane.SATELLITE, "gs-eu", NetworkPlane.CLOUD, "azure-eastus", 80.0, 10.0, 0.02),
            (NetworkPlane.SATELLITE, "gs-jp", NetworkPlane.CLOUD, "aws-ap-northeast-1", 3.0, 25.0, 0.01),
            # Ground station → Edge PoP
            (NetworkPlane.SATELLITE, "gs-tw", NetworkPlane.EDGE, "fly-tpe", 1.0, 10.0, 0.0),
            (NetworkPlane.SATELLITE, "gs-us-west", NetworkPlane.EDGE, "cf-sfo", 1.0, 10.0, 0.0),
            (NetworkPlane.SATELLITE, "gs-jp", NetworkPlane.EDGE, "cf-nrt", 1.0, 10.0, 0.0),
            (NetworkPlane.SATELLITE, "gs-sg", NetworkPlane.EDGE, "cf-sin", 1.0, 10.0, 0.0),
            # Edge PoP → Cloud region
            (NetworkPlane.EDGE, "cf-nrt", NetworkPlane.CLOUD, "aws-ap-northeast-1", 2.0, 25.0, 0.005),
            (NetworkPlane.EDGE, "cf-sfo", NetworkPlane.CLOUD, "gcp-us-central1", 10.0, 25.0, 0.005),
            (NetworkPlane.EDGE, "cf-ams", NetworkPlane.CLOUD, "azure-eastus", 80.0, 25.0, 0.005),
            (NetworkPlane.EDGE, "cf-sin", NetworkPlane.CLOUD, "gcp-asia-east1", 30.0, 25.0, 0.005),
            (NetworkPlane.EDGE, "fly-tpe", NetworkPlane.CLOUD, "gcp-asia-east1", 5.0, 10.0, 0.005),
            (NetworkPlane.EDGE, "vercel-icn", NetworkPlane.CLOUD, "aws-ap-northeast-1", 20.0, 10.0, 0.005),
        ]
        for sp, sn, tp, tn, lat, bw, cost in defaults:
            self.cross_links.append(CrossPlaneLink(
                source_plane=sp, source_node=sn,
                target_plane=tp, target_node=tn,
                latency_ms=lat, bandwidth_gbps=bw, cost_per_gb=cost,
            ))

    def add_cross_link(self, link: CrossPlaneLink) -> None:
        self.cross_links.append(link)

    def route(self, request_id: str, source_layer: LayerID, target_layer: LayerID,
              qos: Optional[Dict] = None) -> RouteDecision:
        """
        Route a request from source_layer to target_layer across planes.

        qos keys: max_latency_ms, max_cost, min_reliability, prefer_plane
        """
        qos = qos or {}
        src_plane = self.layer_map.get(source_layer, NetworkPlane.CLOUD)
        tgt_plane = self.layer_map.get(target_layer, NetworkPlane.CLOUD)

        if src_plane == tgt_plane:
            # Same plane — direct route
            return RouteDecision(
                request_id=request_id,
                source_plane=src_plane, target_plane=tgt_plane,
                source_layer=source_layer, target_layer=target_layer,
                selected_path=[f"{src_plane.value}:direct"],
                estimated_latency_ms=1.0,
                estimated_cost=0.0,
                reliability=0.999,
                reason="same-plane direct",
            )

        # Find cross-plane links connecting src_plane → tgt_plane
        candidates = [
            cl for cl in self.cross_links
            if cl.is_active and cl.source_plane == src_plane and cl.target_plane == tgt_plane
        ]
        is_reversed = False

        # Also consider reverse direction
        if not candidates:
            candidates = [
                cl for cl in self.cross_links
                if cl.is_active and cl.source_plane == tgt_plane and cl.target_plane == src_plane
            ]
            is_reversed = True

        # Also consider two-hop: src → intermediate → tgt
        if not candidates:
            for cl1 in self.cross_links:
                if not cl1.is_active or cl1.source_plane != src_plane:
                    continue
                for cl2 in self.cross_links:
                    if not cl2.is_active or cl2.target_plane != tgt_plane:
                        continue
                    if cl1.target_plane == cl2.source_plane:
                        # Two-hop path found
                        combined_latency = cl1.latency_ms + cl2.latency_ms
                        max_lat = qos.get("max_latency_ms", float("inf"))
                        if combined_latency <= max_lat:
                            decision = RouteDecision(
                                request_id=request_id,
                                source_plane=src_plane, target_plane=tgt_plane,
                                source_layer=source_layer, target_layer=target_layer,
                                selected_path=[
                                    f"{cl1.source_node}→{cl1.target_node}",
                                    f"{cl2.source_node}→{cl2.target_node}",
                                ],
                                estimated_latency_ms=combined_latency,
                                estimated_cost=cl1.cost_per_gb + cl2.cost_per_gb,
                                reliability=0.98,
                                reason="two-hop cross-plane",
                            )
                            self.decisions.append(decision)
                            return decision

        if not candidates:
            decision = RouteDecision(
                request_id=request_id,
                source_plane=src_plane, target_plane=tgt_plane,
                source_layer=source_layer, target_layer=target_layer,
                selected_path=["no-route"],
                estimated_latency_ms=float("inf"),
                estimated_cost=0.0,
                reliability=0.0,
                reason="no cross-plane link available",
            )
            self.decisions.append(decision)
            return decision

        # Score candidates
        max_lat = qos.get("max_latency_ms", float("inf"))
        prefer = qos.get("prefer_plane")

        best = None
        best_score = float("inf")
        for cl in candidates:
            if cl.latency_ms > max_lat:
                continue
            score = cl.latency_ms + cl.cost_per_gb * 100
            if prefer and cl.target_plane.value == prefer:
                score -= 50
            if score < best_score:
                best_score = score
                best = cl

        if not best:
            best = candidates[0]
            best_score = best.latency_ms

        # When using a reverse link, invert the hop direction
        if is_reversed:
            path = [f"{best.target_node}→{best.source_node}"]
        else:
            path = [f"{best.source_node}→{best.target_node}"]

        decision = RouteDecision(
            request_id=request_id,
            source_plane=src_plane, target_plane=tgt_plane,
            source_layer=source_layer, target_layer=target_layer,
            selected_path=path,
            estimated_latency_ms=best.latency_ms,
            estimated_cost=best.cost_per_gb,
            reliability=0.999 if best.bandwidth_gbps >= 10 else 0.99,
            reason=f"best-score={best_score:.1f}",
        )
        self.decisions.append(decision)
        return decision

    def stats(self) -> Dict:
        return {
            "cross_links": len(self.cross_links),
            "active_links": len([cl for cl in self.cross_links if cl.is_active]),
            "decisions_made": len(self.decisions),
            "planes": ["satellite", "cloud", "edge"],
            "layers": [l.value for l in LayerID],
            "origin_signature": self.origin_signature,
        }
