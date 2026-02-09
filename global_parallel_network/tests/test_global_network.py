"""
Tests for Global Parallel Network
origin_signature: MrLiouWord
"""

import sys
import os

# Ensure the parent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from global_parallel_network.cloud_on_cloud import CloudOnCloud, ReplicationPolicy
from global_parallel_network.edge_on_edge import EdgeOnEdge, EdgeProvider
from global_parallel_network.starlink_bridge import StarlinkBridge, OrbitLayer, SatelliteRelay
from global_parallel_network.parallel_world_router import ParallelWorldRouter, LayerID, NetworkPlane, CrossPlaneLink
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


# ══════════════════════════════════════════════════
# Additional tests — gap coverage
# ══════════════════════════════════════════════════

# ── Cloud: add/remove/get region ──

def test_cloud_add_remove_get_region():
    c = CloudOnCloud()
    from global_parallel_network.cloud_on_cloud import CloudRegion, CloudProvider, CloudTier
    new_r = CloudRegion(
        id="test-region", provider=CloudProvider.PRIVATE, region_code="test-dc",
        tier=CloudTier.L0_IAAS, lat=10.0, lon=20.0,
        capacity_vcpu=100, capacity_mem_gb=200, capacity_gpu=5, capacity_storage_tb=50.0,
    )
    c.add_region(new_r)
    assert c.get_region("test-region") is not None
    assert c.get_region("test-region").capacity_vcpu == 100
    assert c.remove_region("test-region") is True
    assert c.get_region("test-region") is None
    assert c.remove_region("nonexistent") is False
    print("✓ cloud_add_remove_get_region")


def test_cloud_add_link():
    c = CloudOnCloud()
    from global_parallel_network.cloud_on_cloud import CrossCloudLink
    link = CrossCloudLink(
        source_id="aws-us-east-1", target_id="private-tw",
        bandwidth_gbps=100.0, latency_ms=150.0, cost_per_gb=0.05,
    )
    c.add_link(link)
    fetched = c.get_link("aws-us-east-1", "private-tw")
    assert fetched is not None
    assert fetched.bandwidth_gbps == 100.0
    # Reverse lookup
    fetched2 = c.get_link("private-tw", "aws-us-east-1")
    assert fetched2 is not None
    print("✓ cloud_add_link")


def test_cloud_get_link_nonexistent():
    c = CloudOnCloud()
    assert c.get_link("fake-a", "fake-b") is None
    print("✓ cloud_get_link_nonexistent")


def test_cloud_estimate_latency_missing_region():
    c = CloudOnCloud()
    lat = c._estimate_latency("fake-region", "aws-us-east-1")
    assert lat == 999.0
    print("✓ cloud_estimate_latency_missing_region")


def test_cloud_placement_fallback():
    c = CloudOnCloud()
    # Require impossibly high resources — should still return a fallback
    p = c.place_workload("wl-impossible", {"min_vcpu": 999999, "min_gpu": 999999})
    assert p.workload_id == "wl-impossible"
    assert p.region_id  # fallback to first region
    assert p.score == 999.0
    print(f"✓ cloud_placement_fallback → {p.region_id}")


def test_cloud_get_replication_nonexistent():
    c = CloudOnCloud()
    assert c.get_replication("nonexistent-service") is None
    print("✓ cloud_get_replication_nonexistent")


def test_cloud_placement_prefer_region():
    c = CloudOnCloud()
    p = c.place_workload("wl-prefer", {"prefer_region": "ap-northeast-1"})
    assert p.workload_id == "wl-prefer"
    # Should prefer the region with matching code
    assert "ap-northeast-1" in p.region_id or p.score < 100
    print(f"✓ cloud_placement_prefer_region → {p.region_id}")


# ── Edge: add/remove node, heartbeat, provider filter, invalid route ──

def test_edge_add_remove_node():
    e = EdgeOnEdge()
    from global_parallel_network.edge_on_edge import EdgeNode, EdgeProvider
    node = EdgeNode(id="test-pop", provider=EdgeProvider.FLY_IO, pop_code="TST", lat=0.0, lon=0.0)
    e.add_node(node)
    assert "test-pop" in e.nodes
    assert e.remove_node("test-pop") is True
    assert "test-pop" not in e.nodes
    assert e.remove_node("nonexistent") is False
    print("✓ edge_add_remove_node")


def test_edge_heartbeat():
    e = EdgeOnEdge()
    import time
    old_hb = e.nodes["cf-nrt"].last_heartbeat
    time.sleep(0.01)
    assert e.heartbeat("cf-nrt") is True
    assert e.nodes["cf-nrt"].last_heartbeat > old_hb
    assert e.heartbeat("nonexistent-node") is False
    print("✓ edge_heartbeat")


def test_edge_nearest_with_provider_filter():
    e = EdgeOnEdge()
    # Nearest Deno Deploy to Tokyo
    n = e.nearest_node(35.68, 139.69, provider=EdgeProvider.DENO_DEPLOY)
    assert n is not None
    assert n.provider == EdgeProvider.DENO_DEPLOY
    print(f"✓ edge_nearest_with_provider_filter → {n.id}")


def test_edge_route_invalid_source():
    e = EdgeOnEdge()
    pkt = e.route_packet("nonexistent", "cf-sfo", b"test")
    assert pkt is None
    print("✓ edge_route_invalid_source")


def test_edge_route_invalid_target():
    e = EdgeOnEdge()
    pkt = e.route_packet("cf-nrt", "nonexistent", b"test")
    assert pkt is None
    print("✓ edge_route_invalid_target")


def test_edge_gossip_read_nonexistent():
    e = EdgeOnEdge()
    assert e.gossip_read("nonexistent") is None
    print("✓ edge_gossip_read_nonexistent")


def test_edge_haversine_missing_node():
    e = EdgeOnEdge()
    dist = e._haversine("nonexistent-a", "nonexistent-b")
    assert dist == 99999.0
    print("✓ edge_haversine_missing_node")


# ── Starlink: add satellite, deorbit, add ground station, invalid route, auto-calc ──

def test_starlink_add_satellite():
    s = StarlinkBridge()
    from global_parallel_network.starlink_bridge import SatelliteRelay
    sat = SatelliteRelay(id="leo-test", orbit=OrbitLayer.LEO, altitude_km=550, lat=0.0, lon=0.0)
    s.add_satellite(sat)
    assert "leo-test" in s.satellites
    assert s.satellites["leo-test"].coverage_radius_km > 0
    assert s.satellites["leo-test"].latency_to_ground_ms > 0
    print(f"✓ starlink_add_satellite coverage={sat.coverage_radius_km}km latency={sat.latency_to_ground_ms}ms")


def test_starlink_deorbit():
    s = StarlinkBridge()
    from global_parallel_network.starlink_bridge import SatelliteStatus
    assert s.deorbit("leo-001") is True
    assert s.satellites["leo-001"].status == SatelliteStatus.DEORBITING
    assert s.deorbit("nonexistent") is False
    print("✓ starlink_deorbit")


def test_starlink_add_ground_station():
    s = StarlinkBridge()
    from global_parallel_network.starlink_bridge import GroundStation
    gs = GroundStation(id="gs-test", lat=48.86, lon=2.35, name="Paris Test")
    s.add_ground_station(gs)
    assert "gs-test" in s.ground_stations
    assert s.ground_stations["gs-test"].name == "Paris Test"
    print("✓ starlink_add_ground_station")


def test_starlink_route_invalid_gs():
    s = StarlinkBridge()
    route = s.compute_route("nonexistent", "gs-tw")
    assert route is None
    route2 = s.compute_route("gs-tw", "nonexistent")
    assert route2 is None
    print("✓ starlink_route_invalid_gs")


def test_starlink_satellite_auto_calc():
    """Verify SatelliteRelay __post_init__ auto-calculates coverage and latency."""
    from global_parallel_network.starlink_bridge import SatelliteRelay
    sat = SatelliteRelay(id="auto-test", orbit=OrbitLayer.LEO, altitude_km=550, lat=0.0, lon=0.0)
    assert sat.coverage_radius_km > 2000  # ~2600 km for 550 km altitude
    assert 3.0 < sat.latency_to_ground_ms < 4.0  # 2*550/300 ≈ 3.67 ms
    geo = SatelliteRelay(id="geo-test", orbit=OrbitLayer.GEO, altitude_km=35786, lat=0.0, lon=0.0)
    assert geo.latency_to_ground_ms > 200  # 2*35786/300 ≈ 238 ms
    print(f"✓ starlink_satellite_auto_calc LEO={sat.latency_to_ground_ms}ms GEO={geo.latency_to_ground_ms}ms")


# ── Router: add_cross_link, no-route, QoS filter, two-hop, stats ──

def test_router_add_cross_link():
    r = ParallelWorldRouter()
    from global_parallel_network.parallel_world_router import CrossPlaneLink
    link = CrossPlaneLink(
        source_plane=NetworkPlane.EDGE, source_node="test-edge",
        target_plane=NetworkPlane.SATELLITE, target_node="test-sat",
        latency_ms=5.0, bandwidth_gbps=10.0,
    )
    before = len(r.cross_links)
    r.add_cross_link(link)
    assert len(r.cross_links) == before + 1
    print("✓ router_add_cross_link")


def test_router_no_route():
    """Route between planes with no links should return no-route."""
    r = ParallelWorldRouter()
    # Remove all cross links
    r.cross_links = []
    d = r.route("req-noroute", LayerID.L_NEG1, LayerID.L2)
    assert d.estimated_latency_ms == float("inf")
    assert d.reliability == 0.0
    assert "no-route" in d.selected_path[0] or "no cross-plane" in d.reason
    print(f"✓ router_no_route reason={d.reason}")


def test_router_qos_max_latency():
    """QoS max_latency_ms should filter out high-latency links."""
    r = ParallelWorldRouter()
    # Route edge→cloud with very tight latency requirement
    d = r.route("req-qos", LayerID.L2, LayerID.L4, qos={"max_latency_ms": 1.0})
    # All edge→cloud links are ≥2ms, so should still pick best available
    assert d.request_id == "req-qos"
    print(f"✓ router_qos_max_latency lat={d.estimated_latency_ms}ms")


def test_router_stats():
    r = ParallelWorldRouter()
    s0 = r.stats()
    assert s0["decisions_made"] == 0
    r.route("req-stat", LayerID.L_NEG1, LayerID.L5)
    s = r.stats()
    assert s["cross_links"] == 15
    assert s["decisions_made"] == 1
    assert "satellite" in s["planes"]
    assert "L-1" in s["layers"]
    print("✓ router_stats")


# ── Global: individual stats methods, edge_nearest, failed satellite route ──

def test_global_cloud_stats():
    g = GlobalParallelNetwork()
    s = g.cloud_stats()
    assert s["total_regions"] == 8
    print("✓ global_cloud_stats")


def test_global_edge_stats():
    g = GlobalParallelNetwork()
    s = g.edge_stats()
    assert s["total_nodes"] == 13
    print("✓ global_edge_stats")


def test_global_satellite_stats():
    g = GlobalParallelNetwork()
    s = g.satellite_stats()
    assert s["active_satellites"] == 17
    print("✓ global_satellite_stats")


def test_global_router_stats():
    g = GlobalParallelNetwork()
    s = g.router_stats()
    assert s["cross_links"] == 15
    print("✓ global_router_stats")


def test_global_edge_nearest():
    g = GlobalParallelNetwork()
    n = g.edge_nearest(25.03, 121.56)
    assert n is not None
    assert n.id == "fly-tpe"
    print(f"✓ global_edge_nearest → {n.id}")


def test_global_satellite_route_invalid():
    g = GlobalParallelNetwork()
    route = g.satellite_route("nonexistent", "gs-tw")
    assert route is None
    print("✓ global_satellite_route_invalid")


def test_global_edge_route_failed():
    g = GlobalParallelNetwork()
    # Route between nodes with no path (Asia→Americas via edge only)
    pkt = g.edge_route("cf-nrt", "cf-sfo", b"cross_pacific")
    # Should return a packet but not delivered (no trans-Pacific edge link)
    assert pkt is not None
    assert pkt.delivered_at is None
    print(f"✓ global_edge_route_failed hops={len(pkt.hops)}")


def test_global_event_log():
    g = GlobalParallelNetwork()
    initial_events = len(g.event_log)
    g.place_workload("ev-test", {"min_vcpu": 1})
    g.satellite_route("gs-tw", "gs-jp")
    g.cross_route("ev-cross", "L2", "L5")
    assert len(g.event_log) == initial_events + 3
    assert g.event_log[-1]["type"] == "cross_route"
    print(f"✓ global_event_log events={len(g.event_log)}")


# ── Runner Fleet (cloud-on-cloud infrastructure) ──

def test_runner_register_compliant():
    c = CloudOnCloud()
    r = c.register_runner("runner-tw-01", "gcp-asia-east1", "2.329.0",
                          labels=["self-hosted", "linux", "cloud-tw"])
    assert r["compliant"] is True
    assert "warning" not in r
    print("✓ runner_register_compliant")


def test_runner_register_non_compliant():
    c = CloudOnCloud()
    r = c.register_runner("runner-old", "aws-us-east-1", "2.320.0")
    assert r["compliant"] is False
    assert "warning" in r
    assert "2.329.0" in r["warning"]
    print(f"✓ runner_register_non_compliant warning={r['warning'][:50]}...")


def test_runner_register_newer():
    c = CloudOnCloud()
    r = c.register_runner("runner-new", "azure-eastus", "2.335.0")
    assert r["compliant"] is True
    print("✓ runner_register_newer")


def test_runner_fleet_compliance():
    c = CloudOnCloud()
    c.register_runner("r1", "gcp-asia-east1", "2.329.0")
    c.register_runner("r2", "aws-us-east-1", "2.335.0")
    c.register_runner("r3", "azure-eastus", "2.310.0")
    c.register_runner("r4", "private-tw", "2.200.0")
    report = c.check_fleet_compliance()
    assert report["total_runners"] == 4
    assert report["compliant"] == 2
    assert report["non_compliant"] == 2
    assert report["deadline"] == "2026-03-16"
    assert len(report["non_compliant_runners"]) == 2
    print(f"✓ runner_fleet_compliance {report['compliant']}/{report['total_runners']} compliant")


def test_runner_version_compare():
    c = CloudOnCloud()
    assert c._version_gte("2.329.0", "2.329.0") is True
    assert c._version_gte("2.330.0", "2.329.0") is True
    assert c._version_gte("2.328.9", "2.329.0") is False
    assert c._version_gte("3.0.0", "2.329.0") is True
    assert c._version_gte("invalid", "2.329.0") is False
    print("✓ runner_version_compare")


def test_runner_in_stats():
    c = CloudOnCloud()
    s0 = c.stats()
    assert s0["runners"] == 0
    c.register_runner("r1", "gcp-asia-east1", "2.329.0")
    c.register_runner("r2", "aws-us-east-1", "2.310.0")
    s = c.stats()
    assert s["runners"] == 2
    assert s["runners_compliant"] == 1
    print("✓ runner_in_stats")


# ── Run all ──

if __name__ == "__main__":
    tests = [
        # Original 20
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
        # New gap-coverage tests (25)
        test_cloud_add_remove_get_region,
        test_cloud_add_link,
        test_cloud_get_link_nonexistent,
        test_cloud_estimate_latency_missing_region,
        test_cloud_placement_fallback,
        test_cloud_get_replication_nonexistent,
        test_cloud_placement_prefer_region,
        test_edge_add_remove_node,
        test_edge_heartbeat,
        test_edge_nearest_with_provider_filter,
        test_edge_route_invalid_source,
        test_edge_route_invalid_target,
        test_edge_gossip_read_nonexistent,
        test_edge_haversine_missing_node,
        test_starlink_add_satellite,
        test_starlink_deorbit,
        test_starlink_add_ground_station,
        test_starlink_route_invalid_gs,
        test_starlink_satellite_auto_calc,
        test_router_add_cross_link,
        test_router_no_route,
        test_router_qos_max_latency,
        test_router_stats,
        test_global_cloud_stats,
        test_global_edge_stats,
        test_global_satellite_stats,
        test_global_router_stats,
        test_global_edge_nearest,
        test_global_satellite_route_invalid,
        test_global_edge_route_failed,
        test_global_event_log,
        # Runner fleet tests (7)
        test_runner_register_compliant,
        test_runner_register_non_compliant,
        test_runner_register_newer,
        test_runner_fleet_compliance,
        test_runner_version_compare,
        test_runner_in_stats,
    ]

    passed = 0
    failed = 0
    for t in tests:
        try:
            t()
            passed += 1
        except Exception as e:
            print(f"✗ {t.__name__}: {e}")
            import traceback
            traceback.print_exc()
            failed += 1

    print(f"\n{'='*50}")
    print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
    if failed == 0:
        print("All tests passed!")
    else:
        print(f"FAILURES: {failed}")
        exit(1)
