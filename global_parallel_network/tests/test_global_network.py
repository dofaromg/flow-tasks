"""
Tests for Global Parallel Network
origin_signature: MrLiouWord
"""

import sys
import os

# Ensure the parent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from global_parallel_network.cloud_on_cloud import CloudOnCloud, CloudProvider, ReplicationPolicy
from global_parallel_network.edge_on_edge import EdgeOnEdge, EdgeProvider, EdgeNodeStatus
from global_parallel_network.starlink_bridge import StarlinkBridge, OrbitLayer
from global_parallel_network.parallel_world_router import ParallelWorldRouter, LayerID, NetworkPlane
from global_parallel_network.global_network import GlobalParallelNetwork


# ── Cloud-on-Cloud ──

def test_cloud_default_regions():
    c = CloudOnCloud()
    s = c.stats()
    assert s["total_regions"] == 8
    assert s["active_regions"] == 8
    assert "aws" in s["providers"]
    assert "gcp" in s["providers"]
    assert "azure" in s["providers"]
    assert "cloudflare" in s["providers"]
    assert "private" in s["providers"]
    print("✓ cloud_default_regions")


def test_cloud_workload_placement():
    c = CloudOnCloud()
    p = c.place_workload("wl-1", {"min_vcpu": 4000, "min_gpu": 100, "prefer_provider": "gcp"})
    assert p.workload_id == "wl-1"
    assert p.region_id  # should pick a region
    assert p.score < 1000
    print(f"✓ cloud_workload_placement → {p.region_id}")


def test_cloud_replication():
    c = CloudOnCloud()
    c.set_replication("particle-db", ReplicationPolicy.ACTIVE_ACTIVE)
    assert c.get_replication("particle-db") == ReplicationPolicy.ACTIVE_ACTIVE
    print("✓ cloud_replication")


def test_cloud_links():
    c = CloudOnCloud()
    link = c.get_link("aws-us-east-1", "gcp-us-central1")
    assert link is not None
    assert link.latency_ms > 0
    print(f"✓ cloud_links latency={link.latency_ms}ms")


# ── Edge-on-Edge ──

def test_edge_default_pops():
    e = EdgeOnEdge()
    s = e.stats()
    assert s["total_nodes"] == 13
    assert s["active_nodes"] == 13
    assert "cloudflare-workers" in s["providers"]
    assert s["total_capacity_rps"] > 1_000_000
    print(f"✓ edge_default_pops nodes={s['total_nodes']} rps={s['total_capacity_rps']:,}")


def test_edge_nearest_node():
    e = EdgeOnEdge()
    # Nearest to Taipei (25.03, 121.56)
    n = e.nearest_node(25.03, 121.56)
    assert n is not None
    assert n.id == "fly-tpe"  # Fly.io TPE is closest
    print(f"✓ edge_nearest_node → {n.id} ({n.pop_code})")


def test_edge_route_packet():
    e = EdgeOnEdge()
    pkt = e.route_packet("cf-nrt", "cf-sfo", b"test_payload")
    # May or may not deliver depending on link topology
    assert pkt is not None
    assert pkt.source_node == "cf-nrt"
    assert len(pkt.hops) >= 1
    print(f"✓ edge_route_packet hops={len(pkt.hops)} delivered={pkt.delivered_at is not None}")


def test_edge_gossip():
    e = EdgeOnEdge()
    e.gossip_update("cf-nrt", {"load": 0.3, "healthy": True})
    state = e.gossip_read("cf-nrt")
    assert state is not None
    assert state["state"]["load"] == 0.3
    merged = e.gossip_merge()
    assert "cf-nrt" in merged
    print("✓ edge_gossip")


# ── Starlink Bridge ──

def test_starlink_constellation():
    s = StarlinkBridge()
    st = s.stats()
    assert st["leo"] == 12
    assert st["meo"] == 2
    assert st["geo"] == 3
    assert st["ground_stations"] == 8
    assert st["total_links"] > 20
    print(f"✓ starlink_constellation sats={st['active_satellites']} gs={st['ground_stations']} links={st['total_links']}")


def test_starlink_route_tw_to_us():
    s = StarlinkBridge()
    route = s.compute_route("gs-tw", "gs-us-west")
    assert route is not None
    assert route.total_latency_ms > 0
    assert len(route.hops) >= 3  # gs → sat(s) → gs
    print(f"✓ starlink_route tw→us latency={route.total_latency_ms}ms hops={route.total_hops}")


def test_starlink_route_tw_to_eu():
    s = StarlinkBridge()
    route = s.compute_route("gs-tw", "gs-eu")
    assert route is not None
    assert route.total_latency_ms > 0
    print(f"✓ starlink_route tw→eu latency={route.total_latency_ms}ms hops={route.total_hops}")


def test_starlink_global_broadcast():
    s = StarlinkBridge()
    results = []
    for gs_id in s.ground_stations:
        if gs_id == "gs-tw":
            continue
        r = s.compute_route("gs-tw", gs_id)
        if r:
            results.append((gs_id, r.total_latency_ms, r.total_hops))
    assert len(results) >= 5
    print(f"✓ starlink_global_broadcast reached {len(results)} stations")
    for gs, lat, hops in sorted(results, key=lambda x: x[1]):
        print(f"    {gs}: {lat}ms ({hops} hops)")


# ── Parallel World Router ──

def test_router_same_plane():
    r = ParallelWorldRouter()
    d = r.route("req-1", LayerID.L0, LayerID.L1)
    assert d.source_plane == NetworkPlane.CLOUD
    assert d.target_plane == NetworkPlane.CLOUD
    assert d.estimated_latency_ms == 1.0
    print("✓ router_same_plane")


def test_router_cross_plane_sat_to_cloud():
    r = ParallelWorldRouter()
    d = r.route("req-2", LayerID.L_NEG1, LayerID.L5)
    assert d.estimated_latency_ms < float("inf")
    assert len(d.selected_path) >= 1
    print(f"✓ router_cross_plane L-1→L5 path={d.selected_path} lat={d.estimated_latency_ms}ms")


def test_router_cross_plane_edge_to_cloud():
    r = ParallelWorldRouter()
    d = r.route("req-3", LayerID.L2, LayerID.L7)
    assert d.estimated_latency_ms < float("inf")
    print(f"✓ router_cross_plane L2→L7 path={d.selected_path} lat={d.estimated_latency_ms}ms")


def test_router_cross_plane_sat_to_edge():
    r = ParallelWorldRouter()
    d = r.route("req-4", LayerID.L_NEG1, LayerID.L2)
    assert d.estimated_latency_ms < float("inf")
    print(f"✓ router_cross_plane L-1→L2 path={d.selected_path} lat={d.estimated_latency_ms}ms")


# ── Global Parallel Network (integration) ──

def test_global_init():
    g = GlobalParallelNetwork()
    s = g.stats()
    assert s["version"] == "1.0.0"
    assert s["cloud"]["total_regions"] == 8
    assert s["edge"]["total_nodes"] == 13
    assert s["starlink"]["active_satellites"] == 17
    assert s["origin_signature"] == "MrLiouWord"
    print("✓ global_init")


def test_global_e2e_tw_to_us():
    g = GlobalParallelNetwork()
    result = g.e2e_route("tw-to-us")
    assert result["scenario"] == "tw-to-us"
    assert result["satellite"]["latency_ms"] is not None
    assert result["cloud"]["region"] is not None
    assert result["cross_plane"]["reliability"] > 0
    print(f"✓ global_e2e tw→us")
    print(f"    satellite: {result['satellite']['latency_ms']}ms via {result['satellite']['path_type']}")
    print(f"    cloud: {result['cloud']['region']} (score={result['cloud']['score']:.1f})")
    print(f"    cross-plane: {result['cross_plane']['path']} lat={result['cross_plane']['latency_ms']}ms")


def test_global_e2e_broadcast():
    g = GlobalParallelNetwork()
    result = g.e2e_route("global-broadcast")
    assert "broadcast" in result
    assert len(result["broadcast"]) >= 5
    print(f"✓ global_e2e broadcast to {len(result['broadcast'])} stations")


def test_global_summary():
    g = GlobalParallelNetwork()
    # Run some operations first
    g.place_workload("test-wl", {"min_vcpu": 4})
    g.satellite_route("gs-tw", "gs-jp")
    g.cross_route("test-cross", "L-1", "L5")
    summary = g.summary()
    assert "Global Parallel Network" in summary
    assert "MrLiouWord" in summary
    print("✓ global_summary")
    print(summary)


# ── Run all ──

if __name__ == "__main__":
    tests = [
        test_cloud_default_regions,
        test_cloud_workload_placement,
        test_cloud_replication,
        test_cloud_links,
        test_edge_default_pops,
        test_edge_nearest_node,
        test_edge_route_packet,
        test_edge_gossip,
        test_starlink_constellation,
        test_starlink_route_tw_to_us,
        test_starlink_route_tw_to_eu,
        test_starlink_global_broadcast,
        test_router_same_plane,
        test_router_cross_plane_sat_to_cloud,
        test_router_cross_plane_edge_to_cloud,
        test_router_cross_plane_sat_to_edge,
        test_global_init,
        test_global_e2e_tw_to_us,
        test_global_e2e_broadcast,
        test_global_summary,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"FAILURES: {failed}")
        exit(1)
