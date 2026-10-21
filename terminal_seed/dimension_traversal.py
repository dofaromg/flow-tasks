"""
Dimension Traversal — Cross-dimension projection and traversal
origin_signature: MrLiouWord

Supports 3D-12D traversal using projection matrices.
Geometry: circumference = 2πr (boundary), area = πr² (state space).
Higher dimensions → state space grows faster than boundary constraints.

LAW-0: origin_signature must be preserved across all transformations.
"""

import math
import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"
MIN_DIM = 3
MAX_DIM = 12


@dataclass
class DimensionMatrix:
    """Projection matrix for dimension traversal."""
    from_dim: int
    to_dim: int
    matrix: List[List[float]]
    topology_preserved: bool = True

    def apply(self, coordinates: List[float]) -> List[float]:
        """Apply the projection matrix to a coordinate vector."""
        if len(coordinates) != self.from_dim:
            raise ValueError(f"Expected {self.from_dim}D coordinates, got {len(coordinates)}D")
        result = []
        for row in self.matrix:
            val = sum(row[j] * coordinates[j] for j in range(min(len(row), len(coordinates))))
            result.append(round(val, 6))
        return result


def calculate_dimension_matrix(from_dim: int, to_dim: int) -> DimensionMatrix:
    """
    Calculate the projection matrix for dimension traversal.

    - Common dimensions: identity mapping (1:1)
    - Expansion (to > from): new dims get small projections from existing dims
    - Compression (to < from): extra dims truncated
    """
    matrix = [[0.0] * from_dim for _ in range(to_dim)]

    common = min(from_dim, to_dim)
    for i in range(common):
        matrix[i][i] = 1.0

    if to_dim > from_dim:
        for i in range(from_dim, to_dim):
            for j in range(from_dim):
                matrix[i][j] = 0.1 * (j + 1) / from_dim

    return DimensionMatrix(
        from_dim=from_dim,
        to_dim=to_dim,
        matrix=matrix,
        topology_preserved=True,
    )


@dataclass
class TraversalResult:
    """Result of a dimension traversal."""
    original_dim: int
    target_dim: int
    original_coordinates: List[float]
    projected_coordinates: List[float]
    topology_preserved: bool
    dimensional_energy: float
    entropy_delta: float
    origin_signature: str = ORIGIN_SIGNATURE


class DimensionTraversal:
    """
    Manages cross-dimension traversal for particles and seeds.

    Supports 3D-12D. Uses projection matrices to map coordinates
    while preserving topological structure.

    Circumference geometry:
      boundary = 2πr (linear growth)
      state_space = πr² (quadratic growth)
      → higher dimensions are more computationally efficient
    """

    def __init__(self):
        self.matrices: Dict[Tuple[int, int], DimensionMatrix] = {}
        self.traversal_log: List[TraversalResult] = []
        self.origin_signature = ORIGIN_SIGNATURE

    def get_matrix(self, from_dim: int, to_dim: int) -> DimensionMatrix:
        """Get or compute the projection matrix."""
        key = (from_dim, to_dim)
        if key not in self.matrices:
            self.matrices[key] = calculate_dimension_matrix(from_dim, to_dim)
        return self.matrices[key]

    def traverse(self, coordinates: List[float], from_dim: int, to_dim: int,
                 properties: Optional[Dict] = None) -> TraversalResult:
        """
        Traverse a point from one dimension to another.

        LAW-0: origin_signature is preserved.
        """
        if from_dim < MIN_DIM or from_dim > MAX_DIM:
            raise ValueError(f"from_dim {from_dim} out of range [{MIN_DIM}, {MAX_DIM}]")
        if to_dim < MIN_DIM or to_dim > MAX_DIM:
            raise ValueError(f"to_dim {to_dim} out of range [{MIN_DIM}, {MAX_DIM}]")
        if len(coordinates) != from_dim:
            raise ValueError(f"coordinates length {len(coordinates)} != from_dim {from_dim}")

        matrix = self.get_matrix(from_dim, to_dim)
        projected = matrix.apply(coordinates)

        # Dimensional energy: based on the magnitude change
        orig_mag = math.sqrt(sum(c * c for c in coordinates))
        proj_mag = math.sqrt(sum(c * c for c in projected))
        dim_energy = round(proj_mag / max(orig_mag, 1e-10), 4)

        # Entropy delta: information change from dimension shift
        entropy_delta = round(abs(to_dim - from_dim) * 0.08 * dim_energy, 4)

        result = TraversalResult(
            original_dim=from_dim,
            target_dim=to_dim,
            original_coordinates=coordinates,
            projected_coordinates=projected,
            topology_preserved=matrix.topology_preserved,
            dimensional_energy=dim_energy,
            entropy_delta=entropy_delta,
        )
        self.traversal_log.append(result)
        return result

    def traverse_particle(self, particle: Dict, from_dim: int, to_dim: int) -> Dict:
        """
        Traverse a particle dict between dimensions.
        Matches the spec's dimensionalTraverse() function.
        """
        sig = particle.get("origin_signature")
        if sig != ORIGIN_SIGNATURE:
            raise ValueError(f"LAW-0 violation: origin_signature={sig}")

        coords = particle.get("coordinates", [0.0] * from_dim)
        result = self.traverse(coords, from_dim, to_dim)

        traversed = dict(particle)
        traversed["coordinates"] = result.projected_coordinates
        traversed["properties"] = dict(particle.get("properties", {}))
        traversed["properties"]["dimensionalEnergy"] = result.dimensional_energy
        traversed["properties"]["entropyDelta"] = result.entropy_delta
        traversed["topologyPreserved"] = result.topology_preserved
        traversed["origin_signature"] = ORIGIN_SIGNATURE
        return traversed

    def circumference_geometry(self, r: float) -> Dict:
        """
        Compute circumference geometry relationships.
        boundary = 2πr, state_space = πr²
        """
        boundary = 2 * math.pi * r
        state_space = math.pi * r * r
        efficiency = state_space / max(boundary, 1e-10)
        return {
            "radius": r,
            "boundary": round(boundary, 6),
            "state_space": round(state_space, 6),
            "efficiency": round(efficiency, 6),
            "interpretation": {
                "boundary": "Terminal closure boundary (LAW-0)",
                "state_space": "Σ state space capacity",
                "center": "Origin point / LAW-0 core",
                "radius": "Complexity / abstraction level",
            },
        }

    def stats(self) -> Dict:
        return {
            "cached_matrices": len(self.matrices),
            "traversals": len(self.traversal_log),
            "supported_range": f"{MIN_DIM}D-{MAX_DIM}D",
            "origin_signature": self.origin_signature,
        }
