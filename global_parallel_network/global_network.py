"""
Global Parallel Network — Top-level Orchestrator
origin_signature: MrLiouWord

Unifies Cloud-on-Cloud, Edge-on-Edge, and Starlink Bridge into a single
global network with cross-plane routing.

This is a standalone simulation system. Integration with particle_satellite_network,
flowos/adapters, and MrLiou_AI_SuperComputer runtime is planned for future versions.

Layer mapping:
  L-1  Starlink / Physical hardware
  L0   Cloud IaaS (AWS, GCP, Azure, CF, Private)
  L1   Meta-Cloud (cloud-on-cloud federation)
  L2   Edge PoPs (CF Workers, Deno, Vercel, Lambda@Edge, Fly.io)
  L3   Meta-Edge (edge-on-edge mesh)
  L4   Application services
  L5   Cognitive / AI layer
  L6   ASI decision layer
  L7   World state Ω
"""

import time
from typing import Dict, List, Optional

from .cloud_on_cloud import CloudOnCloud, WorkloadPlacement
from .edge_on_edge import EdgeOnEdge, EdgeNode, EdgePacket
from .starlink_bridge import StarlinkBridge, SatelliteRoute
from .parallel_world_router import (
    ParallelWorldRouter, RouteDecision, LayerID,
)


class GlobalParallelNetwork:
    """
    Top-level orchestrator for the MRLiou global parallel network.

    Provides a single API surface to:
      - Place workloads across clouds
      - Route packets through the edge mesh
      - Compute satellite relay paths
      - Route cross-plane requests (satellite ↔ edge ↔ cloud)
      - Query unified network stats
    """

    VERSION = "1.0.0"

    def __init__(self):
        self.cloud = CloudOnCloud()
        self.edge = EdgeOnEdge()
        self.starlink = StarlinkBridge()
        self.router = ParallelWorldRouter()
        self.event_log: List[Dict] = []
        self.origin_signature = "MrLiouWord"
        self._log("init", "GlobalParallelNetwork v{} initialized".format(self.VERSION))

    def _log(self, event_type: str, detail: str) -> None:
        self.event_log.append({
            "type": event_type,
            "detail": detail,
            "ts": time.time(),
        })

    # ── Cloud operations ──

    def place_workload(self, workload_id: str, requirements: Dict) -> WorkloadPlacement:
        placement = self.cloud.place_workload(workload_id, requirements)
        self._log("cloud_place", f"{workload_id} → {placement.region_id}")
        return placement

    def cloud_stats(self) -> Dict:
        return self.cloud.stats()

    # ── Edge operations ──

    def edge_route(self, source_pop: str, target_pop: str, payload: bytes) -> Optional[EdgePacket]:
        packet = self.edge.route_packet(source_pop, target_pop, payload)
        if packet and packet.delivered_at:
            self._log("edge_route", f"{source_pop}→{target_pop} hops={len(packet.hops)}")
        return packet

    def edge_nearest(self, lat: float, lon: float) -> Optional[EdgeNode]:
        return self.edge.nearest_node(lat, lon)

    def edge_stats(self) -> Dict:
        return self.edge.stats()

    # ── Satellite operations ──

    def satellite_route(self, source_gs: str, dest_gs: str) -> Optional[SatelliteRoute]:
        route = self.starlink.compute_route(source_gs, dest_gs)
        if route:
            self._log("sat_route",
                       f"{source_gs}→{dest_gs} lat={route.total_latency_ms}ms hops={route.total_hops}")
        return route

    def satellite_stats(self) -> Dict:
        return self.starlink.stats()

    # ── Cross-plane routing ──

    def cross_route(self, request_id: str, source_layer: str, target_layer: str,
                    qos: Optional[Dict] = None) -> RouteDecision:
        src = LayerID(source_layer)
        tgt = LayerID(target_layer)
        decision = self.router.route(request_id, src, tgt, qos)
        self._log("cross_route",
                   f"{source_layer}→{target_layer} path={decision.selected_path} "
                   f"lat={decision.estimated_latency_ms}ms")
        return decision

    def router_stats(self) -> Dict:
        return self.router.stats()

    # ── End-to-end: Taiwan → US via satellite + edge + cloud ──

    def e2e_route(self, scenario: str = "tw-to-us") -> Dict:
        """
        Demonstrate a full end-to-end route across all three planes.

        Example: User in Taiwan → Starlink → Edge PoP → Cloud GPU → Response
        """
        results = {}

        if scenario == "tw-to-us":
            # 1. Satellite: Taiwan ground station → US ground station
            sat_route = self.satellite_route("gs-tw", "gs-us-west")
            results["satellite"] = {
                "hops": sat_route.hops if sat_route else [],
                "latency_ms": sat_route.total_latency_ms if sat_route else None,
                "path_type": sat_route.path_type if sat_route else None,
            }

            # 2. Edge: nearest edge PoP in US → SFO Cloudflare
            edge_pkt = self.edge_route("fly-tpe", "cf-sfo", b"particle_request")
            results["edge"] = {
                "hops": edge_pkt.hops if edge_pkt else [],
                "delivered": edge_pkt.delivered_at is not None if edge_pkt else False,
            }

            # 3. Cloud: place workload on US cloud
            placement = self.place_workload("e2e-compute", {
                "min_vcpu": 8, "min_gpu": 1, "prefer_provider": "gcp",
            })
            results["cloud"] = {
                "region": placement.region_id,
                "score": placement.score,
            }

            # 4. Cross-plane: L-1 → L5 (satellite to AI layer)
            cross = self.cross_route("e2e-cross", "L-1", "L5")
            results["cross_plane"] = {
                "path": cross.selected_path,
                "latency_ms": cross.estimated_latency_ms,
                "reliability": cross.reliability,
            }

        elif scenario == "global-broadcast":
            # Broadcast from Taiwan to all ground stations
            routes = []
            for gs_id in self.starlink.ground_stations:
                if gs_id == "gs-tw":
                    continue
                r = self.satellite_route("gs-tw", gs_id)
                if r:
                    routes.append({
                        "dest": gs_id,
                        "latency_ms": r.total_latency_ms,
                        "hops": len(r.hops),
                    })
            results["broadcast"] = sorted(routes, key=lambda x: x["latency_ms"])

        results["scenario"] = scenario
        results["origin_signature"] = self.origin_signature
        self._log("e2e_route", f"scenario={scenario}")
        return results

    # ── Unified stats ──

    def stats(self) -> Dict:
        return {
            "version": self.VERSION,
            "cloud": self.cloud.stats(),
            "edge": self.edge.stats(),
            "starlink": self.starlink.stats(),
            "router": self.router.stats(),
            "events": len(self.event_log),
            "origin_signature": self.origin_signature,
        }

    def summary(self) -> str:
        s = self.stats()
        lines = [
            f"=== Global Parallel Network v{self.VERSION} ===",
            f"origin_signature: {self.origin_signature}",
            "",
            f"Cloud-on-Cloud (L0-L1):",
            f"  Regions: {s['cloud']['active_regions']}/{s['cloud']['total_regions']}",
            f"  Providers: {', '.join(s['cloud']['providers'])}",
            f"  vCPU: {s['cloud']['total_vcpu']:,}  GPU: {s['cloud']['total_gpu']:,}",
            f"  Links: {s['cloud']['total_links']}",
            "",
            f"Edge-on-Edge (L2-L3):",
            f"  PoPs: {s['edge']['active_nodes']}/{s['edge']['total_nodes']}",
            f"  Providers: {', '.join(s['edge']['providers'])}",
            f"  Capacity: {s['edge']['total_capacity_rps']:,} RPS",
            f"  Links: {s['edge']['total_links']}",
            "",
            f"Starlink Bridge (L-1):",
            f"  Satellites: {s['starlink']['active_satellites']}/{s['starlink']['total_satellites']}",
            f"    LEO: {s['starlink']['leo']}  MEO: {s['starlink']['meo']}  GEO: {s['starlink']['geo']}",
            f"  Ground Stations: {s['starlink']['ground_stations']}",
            f"  Links: {s['starlink']['total_links']}",
            "",
            f"Cross-Plane Router:",
            f"  Cross-links: {s['router']['cross_links']}",
            f"  Decisions: {s['router']['decisions_made']}",
            "",
            f"Total events: {s['events']}",
        ]
        return "\n".join(lines)
