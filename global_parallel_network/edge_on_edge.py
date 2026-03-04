"""
Edge-on-Edge Mesh Layer (邊緣上邊緣)
origin_signature: MrLiouWord

Maps to L2-L3 in the MRLiou layer model.

Architecture:
  L2 edge nodes (Cloudflare Workers, Deno Deploy, Vercel Edge, Lambda@Edge,
  Fastly Compute, Akamai EdgeWorkers) form the base edge fabric.
  L3 Meta-Edge federates them into a unified edge mesh with:
    - Cross-provider edge routing
    - Particle-aware request dispatch
    - Edge-to-edge gossip protocol for state sync
    - Geo-aware failover
"""

import time
import hashlib
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple

from .geo_utils import haversine


class EdgeProvider(Enum):
    CLOUDFLARE = "cloudflare-workers"
    DENO_DEPLOY = "deno-deploy"
    VERCEL_EDGE = "vercel-edge"
    LAMBDA_EDGE = "lambda@edge"
    FASTLY = "fastly-compute"
    AKAMAI = "akamai-edgeworkers"
    FLY_IO = "fly-io"


class EdgeNodeStatus(Enum):
    ACTIVE = "active"
    DRAINING = "draining"
    OFFLINE = "offline"
    WARMING = "warming"


@dataclass
class EdgeNode:
    """A single edge PoP (Point of Presence)."""
    id: str
    provider: EdgeProvider
    pop_code: str                          # e.g. NRT, SFO, AMS
    lat: float = 0.0
    lon: float = 0.0
    status: EdgeNodeStatus = EdgeNodeStatus.ACTIVE
    capacity_rps: int = 100000             # requests per second
    current_rps: int = 0
    memory_mb: int = 128
    services: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    last_heartbeat: float = field(default_factory=time.time)


@dataclass
class EdgeLink:
    """Gossip link between two edge nodes."""
    source_id: str
    target_id: str
    latency_ms: float
    bandwidth_gbps: float = 10.0
    is_active: bool = True


@dataclass
class EdgePacket:
    """A packet routed through the edge mesh."""
    id: str
    source_node: str
    target_node: str
    payload_hash: str
    hops: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)
    delivered_at: Optional[float] = None
    ttl: int = 8


class EdgeOnEdge:
    """
    L3 Meta-Edge mesh controller.

    Federates multiple edge providers into a unified mesh with gossip-based
    state synchronization and geo-aware routing.
    """

    def __init__(self):
        self.nodes: Dict[str, EdgeNode] = {}
        self.links: Dict[Tuple[str, str], EdgeLink] = {}
        self.gossip_state: Dict[str, Dict] = {}
        self.packets_log: List[EdgePacket] = []
        self.origin_signature = "MrLiouWord"
        self._init_default_pops()

    # ── Bootstrap ──

    def _init_default_pops(self):
        pops = [
            # Cloudflare Workers — 300+ PoPs, representative sample
            ("cf-nrt", EdgeProvider.CLOUDFLARE, "NRT", 35.76, 140.39, 500000),
            ("cf-sfo", EdgeProvider.CLOUDFLARE, "SFO", 37.62, -122.38, 500000),
            ("cf-ams", EdgeProvider.CLOUDFLARE, "AMS", 52.31, 4.76, 400000),
            ("cf-sin", EdgeProvider.CLOUDFLARE, "SIN", 1.36, 103.99, 350000),
            ("cf-gru", EdgeProvider.CLOUDFLARE, "GRU", -23.43, -46.47, 300000),
            # Deno Deploy
            ("deno-iad", EdgeProvider.DENO_DEPLOY, "IAD", 38.95, -77.45, 200000),
            ("deno-hnd", EdgeProvider.DENO_DEPLOY, "HND", 35.55, 139.78, 200000),
            # Vercel Edge
            ("vercel-cdg", EdgeProvider.VERCEL_EDGE, "CDG", 49.01, 2.55, 250000),
            ("vercel-icn", EdgeProvider.VERCEL_EDGE, "ICN", 37.46, 126.44, 250000),
            # Lambda@Edge
            ("lambda-iad", EdgeProvider.LAMBDA_EDGE, "IAD", 38.95, -77.45, 300000),
            ("lambda-nrt", EdgeProvider.LAMBDA_EDGE, "NRT", 35.76, 140.39, 300000),
            # Fly.io
            ("fly-tpe", EdgeProvider.FLY_IO, "TPE", 25.08, 121.23, 150000),
            ("fly-lax", EdgeProvider.FLY_IO, "LAX", 33.94, -118.41, 150000),
        ]
        for nid, prov, pop, lat, lon, rps in pops:
            self.nodes[nid] = EdgeNode(
                id=nid, provider=prov, pop_code=pop,
                lat=lat, lon=lon, capacity_rps=rps,
                services=["particle-dispatch", "kv-cache", "wasm-runtime"],
            )

        # Auto-link nodes within 5000 km
        ids = list(self.nodes.keys())
        for i, a in enumerate(ids):
            for b in ids[i + 1:]:
                dist = self._haversine(a, b)
                if dist < 5000:
                    lat_ms = round(dist * 0.01, 2)  # ~10 µs/km for edge
                    self.links[(a, b)] = EdgeLink(
                        source_id=a, target_id=b, latency_ms=lat_ms,
                    )

    def _haversine(self, a_id: str, b_id: str) -> float:
        a, b = self.nodes.get(a_id), self.nodes.get(b_id)
        if not a or not b:
            return 99999.0
        return haversine(a.lat, a.lon, b.lat, b.lon)

    # ── Node management ──

    def add_node(self, node: EdgeNode) -> None:
        self.nodes[node.id] = node

    def remove_node(self, node_id: str) -> bool:
        return self.nodes.pop(node_id, None) is not None

    def heartbeat(self, node_id: str) -> bool:
        node = self.nodes.get(node_id)
        if node:
            node.last_heartbeat = time.time()
            return True
        return False

    # ── Gossip protocol ──

    def gossip_update(self, node_id: str, state: Dict) -> None:
        """Node publishes its local state to the gossip ring."""
        self.gossip_state[node_id] = {
            "state": state,
            "version": time.time(),
            "node_id": node_id,
        }

    def gossip_read(self, node_id: str) -> Optional[Dict]:
        return self.gossip_state.get(node_id)

    def gossip_merge(self) -> Dict[str, Dict]:
        """Merge all gossip states (crdt-style last-writer-wins)."""
        return dict(self.gossip_state)

    # ── Routing ──

    def nearest_node(self, lat: float, lon: float, provider: Optional[EdgeProvider] = None) -> Optional[EdgeNode]:
        """Find the nearest active edge node to a given coordinate."""
        best = None
        best_dist = float("inf")
        for n in self.nodes.values():
            if n.status != EdgeNodeStatus.ACTIVE:
                continue
            if provider and n.provider != provider:
                continue
            dist = haversine(lat, lon, n.lat, n.lon)
            if dist < best_dist:
                best_dist = dist
                best = n
        return best

    def route_packet(self, source_id: str, target_id: str, payload: bytes) -> Optional[EdgePacket]:
        """Route a packet through the edge mesh using greedy geographic forwarding."""
        if source_id not in self.nodes or target_id not in self.nodes:
            return None

        # Compute hash once and reuse to avoid redundant SHA-256 calls.
        payload_digest = hashlib.sha256(payload).hexdigest()
        packet = EdgePacket(
            id=payload_digest[:16],
            source_node=source_id,
            target_node=target_id,
            payload_hash=payload_digest,
            hops=[source_id],
        )

        current = source_id
        target = self.nodes[target_id]
        visited: Set[str] = {source_id}

        # Build adjacency index once per routing call instead of scanning all
        # links on every hop, reducing per-hop cost from O(links) to O(degree).
        adj: Dict[str, List[str]] = {}
        for (a, b), link in self.links.items():
            if not link.is_active:
                continue
            node_b = self.nodes.get(b)
            if node_b and node_b.status == EdgeNodeStatus.ACTIVE:
                adj.setdefault(a, []).append(b)
            node_a = self.nodes.get(a)
            if node_a and node_a.status == EdgeNodeStatus.ACTIVE:
                adj.setdefault(b, []).append(a)

        while current != target_id and packet.ttl > 0:
            # Find neighbor closest to target
            neighbors = adj.get(current, [])
            best_next = None
            best_dist = float("inf")
            for nb in neighbors:
                if nb in visited:
                    continue
                n = self.nodes[nb]
                dist = haversine(n.lat, n.lon, target.lat, target.lon)
                if dist < best_dist:
                    best_dist = dist
                    best_next = nb

            if not best_next:
                break  # no route

            visited.add(best_next)
            packet.hops.append(best_next)
            packet.ttl -= 1
            current = best_next

        if current == target_id:
            packet.delivered_at = time.time()

        self.packets_log.append(packet)
        return packet

    def _get_neighbors(self, node_id: str) -> List[str]:
        neighbors: List[str] = []
        # Only consider links that are active, and only return neighbors whose nodes are ACTIVE.
        for (a, b), link in self.links.items():
            if not link.is_active:
                continue
            if a == node_id:
                neighbor_id = b
            elif b == node_id:
                neighbor_id = a
            else:
                continue
            neighbor_node = self.nodes.get(neighbor_id)
            if neighbor_node is None or neighbor_node.status != EdgeNodeStatus.ACTIVE:
                continue
            neighbors.append(neighbor_id)
        return neighbors

    # ── Stats ──

    def stats(self) -> Dict:
        active = [n for n in self.nodes.values() if n.status == EdgeNodeStatus.ACTIVE]
        providers = set(n.provider.value for n in active)
        total_rps = sum(n.capacity_rps for n in active)
        return {
            "total_nodes": len(self.nodes),
            "active_nodes": len(active),
            "providers": sorted(providers),
            "total_capacity_rps": total_rps,
            "total_links": len(self.links),
            "gossip_entries": len(self.gossip_state),
            "packets_routed": len(self.packets_log),
            "origin_signature": self.origin_signature,
        }
