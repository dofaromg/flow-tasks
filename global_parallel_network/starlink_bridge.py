"""
Starlink Bridge — Satellite Relay Integration (星鏈橋接)
origin_signature: MrLiouWord

Maps to L-1 (物理硬體) in the MRLiou layer model.

Integrates LEO/MEO/GEO satellite constellations with ground stations
and edge/cloud layers. Provides:
  - Multi-orbit relay (LEO ↔ MEO ↔ GEO)
  - Ground station uplink/downlink
  - Inter-satellite laser links
  - Handover management as satellites move
  - Latency-aware path selection
"""

import time
import math
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .geo_utils import haversine


class OrbitLayer(Enum):
    LEO = "LEO"    # ~550 km (Starlink)
    MEO = "MEO"    # ~20,200 km (GPS-like)
    GEO = "GEO"    # ~35,786 km (geostationary)
    GROUND = "GROUND"


class SatelliteStatus(Enum):
    ACTIVE = "active"
    TRANSITING = "transiting"
    ECLIPSE = "eclipse"
    DEORBITING = "deorbiting"
    OFFLINE = "offline"


@dataclass
class SatelliteRelay:
    """A satellite node in the constellation."""
    id: str
    orbit: OrbitLayer
    altitude_km: float
    lat: float
    lon: float
    inclination_deg: float = 53.0          # Starlink shell 1
    status: SatelliteStatus = SatelliteStatus.ACTIVE
    laser_links: List[str] = field(default_factory=list)  # connected sat IDs
    bandwidth_gbps: float = 20.0
    latency_to_ground_ms: float = 0.0
    coverage_radius_km: float = 0.0
    metadata: Dict[str, str] = field(default_factory=dict)
    launched_at: float = field(default_factory=time.time)

    def __post_init__(self):
        if self.coverage_radius_km == 0.0:
            # Approximate coverage radius from altitude
            self.coverage_radius_km = round(
                math.sqrt((6371 + self.altitude_km) ** 2 - 6371 ** 2), 1
            )
        if self.latency_to_ground_ms == 0.0:
            # Speed of light round-trip: 2 * altitude / c
            self.latency_to_ground_ms = round(2 * self.altitude_km / 300.0, 2)


@dataclass
class GroundStation:
    """A ground station that connects to satellites."""
    id: str
    lat: float
    lon: float
    name: str = ""
    connected_sats: List[str] = field(default_factory=list)
    uplink_gbps: float = 10.0
    downlink_gbps: float = 10.0
    is_active: bool = True


@dataclass
class SatelliteLink:
    """Inter-satellite or sat-to-ground link."""
    source_id: str
    target_id: str
    link_type: str  # "laser", "rf", "uplink", "downlink"
    latency_ms: float
    bandwidth_gbps: float
    is_active: bool = True


@dataclass
class SatelliteRoute:
    """A computed route through the constellation."""
    source: str
    destination: str
    hops: List[str]
    total_latency_ms: float
    total_hops: int
    path_type: str  # "ground-leo-ground", "ground-leo-meo-leo-ground", etc.
    computed_at: float = field(default_factory=time.time)


class StarlinkBridge:
    """
    Satellite constellation bridge.

    Manages LEO/MEO/GEO satellites, ground stations, and inter-satellite
    links. Computes optimal routes through the constellation.
    """

    def __init__(self):
        self.satellites: Dict[str, SatelliteRelay] = {}
        self.ground_stations: Dict[str, GroundStation] = {}
        self.links: Dict[Tuple[str, str], SatelliteLink] = {}
        self.routes_log: List[SatelliteRoute] = []
        self.origin_signature = "MrLiouWord"
        self._adj_cache: Optional[Dict[str, List[Tuple[str, float]]]] = None
        self._init_constellation()

    # ── Bootstrap ──

    def _init_constellation(self):
        # LEO shell (Starlink-like, 550 km, 53° inclination)
        leo_sats = [
            ("leo-001", 550, 25.0, 121.5, 53.0),   # over Taiwan
            ("leo-002", 550, 35.7, 139.7, 53.0),    # over Tokyo
            ("leo-003", 550, 37.6, -122.4, 53.0),   # over San Francisco
            ("leo-004", 550, 52.5, 13.4, 53.0),     # over Berlin
            ("leo-005", 550, -33.9, 151.2, 53.0),   # over Sydney
            ("leo-006", 550, 1.3, 103.8, 53.0),     # over Singapore
            ("leo-007", 550, 55.8, 37.6, 53.0),     # over Moscow
            ("leo-008", 550, -23.5, -46.6, 53.0),   # over São Paulo
            ("leo-009", 550, 28.6, 77.2, 53.0),     # over Delhi
            ("leo-010", 550, 51.5, -0.1, 53.0),     # over London
            ("leo-011", 550, 40.7, -74.0, 53.0),    # over New York
            ("leo-012", 550, -1.3, 36.8, 53.0),     # over Nairobi
        ]
        for sid, alt, lat, lon, inc in leo_sats:
            self.satellites[sid] = SatelliteRelay(
                id=sid, orbit=OrbitLayer.LEO, altitude_km=alt,
                lat=lat, lon=lon, inclination_deg=inc,
                bandwidth_gbps=20.0,
            )

        # MEO relay (2 satellites for inter-orbit relay)
        for i, (lat, lon) in enumerate([(0.0, 0.0), (0.0, 180.0)]):
            sid = f"meo-{i+1:03d}"
            self.satellites[sid] = SatelliteRelay(
                id=sid, orbit=OrbitLayer.MEO, altitude_km=20200,
                lat=lat, lon=lon, inclination_deg=55.0,
                bandwidth_gbps=40.0,
            )

        # GEO relay (3 satellites for global coverage)
        for i, lon in enumerate([0.0, 120.0, -120.0]):
            sid = f"geo-{i+1:03d}"
            self.satellites[sid] = SatelliteRelay(
                id=sid, orbit=OrbitLayer.GEO, altitude_km=35786,
                lat=0.0, lon=lon, inclination_deg=0.0,
                bandwidth_gbps=50.0,
            )

        # Ground stations
        gs_data = [
            ("gs-tw", 25.03, 121.56, "Taiwan Datacenter"),
            ("gs-us-west", 37.77, -122.42, "US West"),
            ("gs-us-east", 38.90, -77.04, "US East"),
            ("gs-eu", 52.52, 13.41, "Europe Central"),
            ("gs-jp", 35.68, 139.69, "Japan"),
            ("gs-sg", 1.35, 103.82, "Singapore"),
            ("gs-au", -33.87, 151.21, "Australia"),
            ("gs-br", -23.55, -46.63, "Brazil"),
        ]
        for gid, lat, lon, name in gs_data:
            self.ground_stations[gid] = GroundStation(
                id=gid, lat=lat, lon=lon, name=name,
            )

        # Auto-connect: ground stations to nearest LEO sats
        for gs in self.ground_stations.values():
            nearest = self._find_nearest_sats(gs.lat, gs.lon, OrbitLayer.LEO, n=3)
            for sat in nearest:
                gs.connected_sats.append(sat.id)
                self.links[(gs.id, sat.id)] = SatelliteLink(
                    source_id=gs.id, target_id=sat.id,
                    link_type="uplink",
                    latency_ms=sat.latency_to_ground_ms,
                    bandwidth_gbps=min(gs.uplink_gbps, sat.bandwidth_gbps),
                )

        # Auto-connect: LEO inter-satellite laser links (neighbors within 5000 km)
        leo_ids = [s.id for s in self.satellites.values() if s.orbit == OrbitLayer.LEO]
        for i, a in enumerate(leo_ids):
            for b in leo_ids[i + 1:]:
                dist = haversine(
                    self.satellites[a].lat, self.satellites[a].lon,
                    self.satellites[b].lat, self.satellites[b].lon,
                )
                if dist < 5000:
                    lat_ms = round(dist / 300.0, 2)  # laser speed ≈ c
                    self.links[(a, b)] = SatelliteLink(
                        source_id=a, target_id=b,
                        link_type="laser",
                        latency_ms=lat_ms,
                        bandwidth_gbps=20.0,
                    )
                    self.satellites[a].laser_links.append(b)
                    self.satellites[b].laser_links.append(a)

        # LEO ↔ MEO relay links
        for meo in [s for s in self.satellites.values() if s.orbit == OrbitLayer.MEO]:
            nearest_leos = self._find_nearest_sats(meo.lat, meo.lon, OrbitLayer.LEO, n=4)
            for leo in nearest_leos:
                lat_ms = round((meo.altitude_km - leo.altitude_km) / 300.0, 2)
                self.links[(leo.id, meo.id)] = SatelliteLink(
                    source_id=leo.id, target_id=meo.id,
                    link_type="laser",
                    latency_ms=lat_ms,
                    bandwidth_gbps=40.0,
                )

    def _find_nearest_sats(self, lat: float, lon: float, orbit: OrbitLayer, n: int = 3) -> List[SatelliteRelay]:
        sats = [(s, haversine(lat, lon, s.lat, s.lon))
                for s in self.satellites.values()
                if s.orbit == orbit and s.status == SatelliteStatus.ACTIVE]
        sats.sort(key=lambda x: x[1])
        return [s for s, _ in sats[:n]]

    def _invalidate_adj_cache(self) -> None:
        """Invalidate the cached adjacency list when the link topology changes."""
        self._adj_cache = None

    def _get_adj(self) -> Dict[str, List[Tuple[str, float]]]:
        """Return (building once) the adjacency dict used by Dijkstra routing.

        The cache is valid as long as the link topology does not change.
        Call _invalidate_adj_cache() before adding, removing, or toggling
        links to ensure the next routing call sees the updated topology.
        """
        if self._adj_cache is None:
            adj: Dict[str, List[Tuple[str, float]]] = {}
            for (a, b), link in self.links.items():
                if not link.is_active:
                    continue
                adj.setdefault(a, []).append((b, link.latency_ms))
                adj.setdefault(b, []).append((a, link.latency_ms))
            self._adj_cache = adj
        return self._adj_cache

    # ── Routing ──

    def compute_route(self, source_gs: str, dest_gs: str) -> Optional[SatelliteRoute]:
        """
        Compute optimal route between two ground stations through the constellation.
        Uses a latency-weighted shortest path search (Dijkstra) over the active link graph.
        """
        if source_gs not in self.ground_stations or dest_gs not in self.ground_stations:
            return None

        # Use cached adjacency list to avoid O(links) rebuild on every call.
        adj = self._get_adj()

        # Dijkstra
        import heapq
        dist: Dict[str, float] = {source_gs: 0.0}
        prev: Dict[str, Optional[str]] = {source_gs: None}
        pq = [(0.0, source_gs)]

        while pq:
            d, u = heapq.heappop(pq)
            if u == dest_gs:
                break
            if d > dist.get(u, float("inf")):
                continue
            for v, w in adj.get(u, []):
                nd = d + w
                if nd < dist.get(v, float("inf")):
                    dist[v] = nd
                    prev[v] = u
                    heapq.heappush(pq, (nd, v))

        if dest_gs not in prev:
            return None

        # Reconstruct path
        path = []
        cur: Optional[str] = dest_gs
        while cur is not None:
            path.append(cur)
            cur = prev.get(cur)
        path.reverse()

        # Determine path type
        orbits_in_path = set()
        for node_id in path:
            if node_id in self.satellites:
                orbits_in_path.add(self.satellites[node_id].orbit.value)
            elif node_id in self.ground_stations:
                orbits_in_path.add("GROUND")

        path_type = "-".join(sorted(orbits_in_path)).lower()

        route = SatelliteRoute(
            source=source_gs,
            destination=dest_gs,
            hops=path,
            total_latency_ms=round(dist.get(dest_gs, 0.0), 2),
            total_hops=len(path) - 1,
            path_type=path_type,
        )
        self.routes_log.append(route)
        return route

    # ── Satellite management ──

    def add_satellite(self, sat: SatelliteRelay) -> None:
        self.satellites[sat.id] = sat

    def deorbit(self, sat_id: str) -> bool:
        sat = self.satellites.get(sat_id)
        if sat:
            sat.status = SatelliteStatus.DEORBITING
            return True
        return False

    def add_ground_station(self, gs: GroundStation) -> None:
        self.ground_stations[gs.id] = gs

    # ── Stats ──

    def stats(self) -> Dict:
        active_sats = [s for s in self.satellites.values() if s.status == SatelliteStatus.ACTIVE]
        leo = len([s for s in active_sats if s.orbit == OrbitLayer.LEO])
        meo = len([s for s in active_sats if s.orbit == OrbitLayer.MEO])
        geo = len([s for s in active_sats if s.orbit == OrbitLayer.GEO])
        return {
            "total_satellites": len(self.satellites),
            "active_satellites": len(active_sats),
            "leo": leo,
            "meo": meo,
            "geo": geo,
            "ground_stations": len(self.ground_stations),
            "total_links": len(self.links),
            "routes_computed": len(self.routes_log),
            "origin_signature": self.origin_signature,
        }
