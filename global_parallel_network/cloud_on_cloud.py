"""
Cloud-on-Cloud Federation Layer (雲上雲)
origin_signature: MrLiouWord

Maps to L0 (雲端基礎) and L1 (雲上雲 Meta-Cloud) in the MRLiou layer model.

Architecture:
  L0 clouds (AWS, GCP, Azure, Cloudflare, Private) each expose a CloudRegion.
  L1 Meta-Cloud federates them into a single control plane with:
    - Cross-cloud service mesh
    - Unified identity / auth propagation
    - Data replication policies (active-active, active-passive, read-replica)
    - Cost-aware workload placement
"""

import time
import hashlib
import uuid
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


class CloudTier(Enum):
    L0_IAAS = "L0_IaaS"
    L0_PAAS = "L0_PaaS"
    L1_META = "L1_Meta-Cloud"


class CloudProvider(Enum):
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    CLOUDFLARE = "cloudflare"
    PRIVATE = "private"


class ReplicationPolicy(Enum):
    ACTIVE_ACTIVE = "active-active"
    ACTIVE_PASSIVE = "active-passive"
    READ_REPLICA = "read-replica"
    EVENTUAL = "eventual"


@dataclass
class CloudRegion:
    """A single cloud region (L0 node)."""
    id: str
    provider: CloudProvider
    region_code: str                       # e.g. us-east-1, asia-east1
    tier: CloudTier = CloudTier.L0_IAAS
    lat: float = 0.0
    lon: float = 0.0
    capacity_vcpu: int = 0
    capacity_mem_gb: int = 0
    capacity_gpu: int = 0
    capacity_storage_tb: float = 0.0
    utilization: float = 0.0               # 0-1
    is_active: bool = True
    services: List[str] = field(default_factory=list)
    metadata: Dict[str, str] = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)


@dataclass
class CrossCloudLink:
    """Network link between two cloud regions."""
    source_id: str
    target_id: str
    bandwidth_gbps: float
    latency_ms: float
    cost_per_gb: float = 0.0
    encrypted: bool = True
    is_active: bool = True


@dataclass
class WorkloadPlacement:
    """Decision record for placing a workload."""
    workload_id: str
    region_id: str
    reason: str
    score: float
    timestamp: float = field(default_factory=time.time)


class CloudOnCloud:
    """
    L1 Meta-Cloud federation controller.

    Federates multiple L0 cloud regions into a unified control plane.
    Provides cross-cloud routing, replication, and cost-aware placement.
    """

    def __init__(self):
        self.regions: Dict[str, CloudRegion] = {}
        self.links: Dict[Tuple[str, str], CrossCloudLink] = {}
        self.placements: List[WorkloadPlacement] = []
        self.replication_policies: Dict[str, ReplicationPolicy] = {}
        self.origin_signature = "MrLiouWord"
        self._init_default_regions()

    # ── Bootstrap ──

    def _init_default_regions(self):
        defaults = [
            ("aws-us-east-1", CloudProvider.AWS, "us-east-1", 39.0, -77.0,
             10000, 40000, 500, 2000.0),
            ("aws-ap-northeast-1", CloudProvider.AWS, "ap-northeast-1", 35.68, 139.69,
             8000, 32000, 400, 1500.0),
            ("gcp-us-central1", CloudProvider.GCP, "us-central1", 41.26, -95.86,
             12000, 48000, 600, 2500.0),
            ("gcp-asia-east1", CloudProvider.GCP, "asia-east1", 25.05, 121.55,
             6000, 24000, 300, 1000.0),
            ("azure-eastus", CloudProvider.AZURE, "eastus", 37.37, -79.15,
             9000, 36000, 450, 1800.0),
            ("azure-japaneast", CloudProvider.AZURE, "japaneast", 35.68, 139.77,
             5000, 20000, 200, 800.0),
            ("cf-global", CloudProvider.CLOUDFLARE, "global", 0.0, 0.0,
             0, 0, 0, 0.0),
            ("private-tw", CloudProvider.PRIVATE, "tw-datacenter", 25.03, 121.56,
             2000, 8000, 100, 500.0),
        ]
        for rid, prov, code, lat, lon, vcpu, mem, gpu, stor in defaults:
            self.regions[rid] = CloudRegion(
                id=rid, provider=prov, region_code=code,
                lat=lat, lon=lon,
                capacity_vcpu=vcpu, capacity_mem_gb=mem,
                capacity_gpu=gpu, capacity_storage_tb=stor,
                services=["compute", "storage", "network"],
            )

        # Default cross-cloud links
        region_ids = list(self.regions.keys())
        for i, a in enumerate(region_ids):
            for b in region_ids[i + 1:]:
                self.links[(a, b)] = CrossCloudLink(
                    source_id=a, target_id=b,
                    bandwidth_gbps=25.0, latency_ms=self._estimate_latency(a, b),
                )

    def _estimate_latency(self, a_id: str, b_id: str) -> float:
        a, b = self.regions.get(a_id), self.regions.get(b_id)
        if not a or not b:
            return 999.0
        # Rough great-circle estimate: ~0.05 ms per km of fiber
        import math
        dlat = math.radians(b.lat - a.lat)
        dlon = math.radians(b.lon - a.lon)
        h = (math.sin(dlat / 2) ** 2 +
             math.cos(math.radians(a.lat)) * math.cos(math.radians(b.lat)) *
             math.sin(dlon / 2) ** 2)
        km = 2 * 6371 * math.asin(math.sqrt(h))
        return round(km * 0.05, 2)

    # ── Region management ──

    def add_region(self, region: CloudRegion) -> None:
        self.regions[region.id] = region

    def remove_region(self, region_id: str) -> bool:
        return self.regions.pop(region_id, None) is not None

    def get_region(self, region_id: str) -> Optional[CloudRegion]:
        return self.regions.get(region_id)

    # ── Link management ──

    def add_link(self, link: CrossCloudLink) -> None:
        self.links[(link.source_id, link.target_id)] = link

    def get_link(self, a: str, b: str) -> Optional[CrossCloudLink]:
        return self.links.get((a, b)) or self.links.get((b, a))

    # ── Workload placement ──

    def place_workload(self, workload_id: str, requirements: Dict) -> WorkloadPlacement:
        """
        Cost-and-latency-aware placement.

        requirements keys: min_vcpu, min_mem_gb, min_gpu, prefer_provider,
                           prefer_region, max_latency_ms
        """
        best_region = None
        best_score = float("inf")

        for r in self.regions.values():
            if not r.is_active:
                continue
            if r.capacity_vcpu < requirements.get("min_vcpu", 0):
                continue
            if r.capacity_mem_gb < requirements.get("min_mem_gb", 0):
                continue
            if r.capacity_gpu < requirements.get("min_gpu", 0):
                continue

            score = r.utilization * 100
            if r.provider.value == requirements.get("prefer_provider"):
                score -= 20
            if r.region_code == requirements.get("prefer_region"):
                score -= 30
            if score < best_score:
                best_score = score
                best_region = r

        if not best_region:
            best_region = next(iter(self.regions.values()))
            best_score = 999.0

        placement = WorkloadPlacement(
            workload_id=workload_id,
            region_id=best_region.id,
            reason=f"score={best_score:.1f} util={best_region.utilization:.2f}",
            score=best_score,
        )
        self.placements.append(placement)
        return placement

    # ── Replication ──

    def set_replication(self, service: str, policy: ReplicationPolicy) -> None:
        self.replication_policies[service] = policy

    def get_replication(self, service: str) -> Optional[ReplicationPolicy]:
        return self.replication_policies.get(service)

    # ── Stats ──

    def stats(self) -> Dict:
        active = [r for r in self.regions.values() if r.is_active]
        providers = set(r.provider.value for r in active)
        total_vcpu = sum(r.capacity_vcpu for r in active)
        total_gpu = sum(r.capacity_gpu for r in active)
        return {
            "total_regions": len(self.regions),
            "active_regions": len(active),
            "providers": sorted(providers),
            "total_vcpu": total_vcpu,
            "total_gpu": total_gpu,
            "total_links": len(self.links),
            "placements": len(self.placements),
            "replication_policies": len(self.replication_policies),
            "origin_signature": self.origin_signature,
        }
