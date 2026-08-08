"""Tests for Dimension Traversal — 3D-12D projection. origin_signature: MrLiouWord"""
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import math
import pytest
from terminal_seed.dimension_traversal import (
    DimensionTraversal, DimensionMatrix, calculate_dimension_matrix,
    TraversalResult, MIN_DIM, MAX_DIM, ORIGIN_SIGNATURE,
)


# ── DimensionMatrix ──

def test_identity_matrix_same_dim():
    m = calculate_dimension_matrix(3, 3)
    assert m.from_dim == 3
    assert m.to_dim == 3
    coords = [1.0, 2.0, 3.0]
    result = m.apply(coords)
    assert result == coords


def test_expansion_matrix():
    m = calculate_dimension_matrix(3, 5)
    assert len(m.matrix) == 5
    assert len(m.matrix[0]) == 3
    coords = [1.0, 0.0, 0.0]
    result = m.apply(coords)
    assert len(result) == 5
    # First 3 dims: identity
    assert result[0] == 1.0
    assert result[1] == 0.0
    assert result[2] == 0.0
    # Extra dims: small projections
    assert result[3] != 0.0
    assert result[4] != 0.0


def test_compression_matrix():
    m = calculate_dimension_matrix(5, 3)
    assert len(m.matrix) == 3
    coords = [1.0, 2.0, 3.0, 4.0, 5.0]
    result = m.apply(coords)
    assert len(result) == 3
    # First 3 dims preserved via identity
    assert result[0] == 1.0
    assert result[1] == 2.0
    assert result[2] == 3.0


def test_matrix_wrong_dim_raises():
    m = calculate_dimension_matrix(3, 5)
    with pytest.raises(ValueError, match="Expected 3D"):
        m.apply([1.0, 2.0])  # wrong length


def test_topology_preserved_flag():
    m = calculate_dimension_matrix(4, 8)
    assert m.topology_preserved is True


# ── DimensionTraversal ──

def test_traverse_3d_to_5d():
    dt = DimensionTraversal()
    result = dt.traverse([1.0, 2.0, 3.0], 3, 5)
    assert isinstance(result, TraversalResult)
    assert result.original_dim == 3
    assert result.target_dim == 5
    assert len(result.projected_coordinates) == 5
    assert result.topology_preserved is True
    assert result.origin_signature == ORIGIN_SIGNATURE


def test_traverse_12d_to_3d():
    dt = DimensionTraversal()
    coords = [float(i) for i in range(12)]
    result = dt.traverse(coords, 12, 3)
    assert len(result.projected_coordinates) == 3
    assert result.dimensional_energy > 0


def test_traverse_same_dim():
    dt = DimensionTraversal()
    coords = [1.0, 2.0, 3.0, 4.0]
    result = dt.traverse(coords, 4, 4)
    assert result.projected_coordinates == coords
    assert result.entropy_delta == 0.0  # no dim change


def test_traverse_out_of_range_from():
    dt = DimensionTraversal()
    with pytest.raises(ValueError, match="from_dim 2 out of range"):
        dt.traverse([1.0, 2.0], 2, 3)


def test_traverse_out_of_range_to():
    dt = DimensionTraversal()
    with pytest.raises(ValueError, match="to_dim 13 out of range"):
        dt.traverse([1.0, 2.0, 3.0], 3, 13)


def test_traverse_wrong_coord_length():
    dt = DimensionTraversal()
    with pytest.raises(ValueError, match="coordinates length"):
        dt.traverse([1.0, 2.0], 3, 5)


def test_traverse_particle():
    dt = DimensionTraversal()
    particle = {
        "id": "p1",
        "coordinates": [1.0, 2.0, 3.0],
        "properties": {},
        "origin_signature": ORIGIN_SIGNATURE,
    }
    result = dt.traverse_particle(particle, 3, 6)
    assert len(result["coordinates"]) == 6
    assert result["origin_signature"] == ORIGIN_SIGNATURE
    assert result["topologyPreserved"] is True
    assert "dimensionalEnergy" in result["properties"]


def test_traverse_particle_law0_violation():
    dt = DimensionTraversal()
    particle = {
        "coordinates": [1.0, 2.0, 3.0],
        "origin_signature": "WRONG",
    }
    with pytest.raises(ValueError, match="LAW-0"):
        dt.traverse_particle(particle, 3, 5)


def test_circumference_geometry():
    dt = DimensionTraversal()
    g = dt.circumference_geometry(5.0)
    assert abs(g["boundary"] - 2 * math.pi * 5.0) < 0.001
    assert abs(g["state_space"] - math.pi * 25.0) < 0.001
    assert g["efficiency"] > 0


def test_traversal_log():
    dt = DimensionTraversal()
    dt.traverse([1.0, 2.0, 3.0], 3, 5)
    dt.traverse([1.0, 2.0, 3.0, 4.0], 4, 7)
    assert len(dt.traversal_log) == 2


def test_matrix_caching():
    dt = DimensionTraversal()
    dt.traverse([1.0, 2.0, 3.0], 3, 5)
    dt.traverse([4.0, 5.0, 6.0], 3, 5)
    # Same (3,5) pair should be cached
    assert len(dt.matrices) == 1


def test_stats():
    dt = DimensionTraversal()
    dt.traverse([1.0, 2.0, 3.0], 3, 5)
    s = dt.stats()
    assert s["cached_matrices"] == 1
    assert s["traversals"] == 1
    assert s["supported_range"] == "3D-12D"
    assert s["origin_signature"] == ORIGIN_SIGNATURE


def test_all_supported_dimensions():
    """Traverse between every supported dimension pair."""
    dt = DimensionTraversal()
    for from_d in range(MIN_DIM, MAX_DIM + 1):
        for to_d in range(MIN_DIM, MAX_DIM + 1):
            coords = [1.0] * from_d
            result = dt.traverse(coords, from_d, to_d)
            assert len(result.projected_coordinates) == to_d
            assert result.topology_preserved is True
