#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_CanonicalProjection_v1.py

Purpose
-------
Keep presentation sovereignty separate from source provenance.

- MRL-owned interfaces display MRL canonical identity.
- External names/origins remain preserved as source metadata.
- External writes are represented as shadow/proposed state.
- No external alias may overwrite canonical identity or history.

origin_signature: MrLiouWord
"""
from __future__ import annotations

from copy import deepcopy
from typing import Any, Dict, Mapping, Optional

ORIGIN_SIGNATURE = "MrLiouWord"


class CanonicalProjectionError(ValueError):
    pass


def _require_text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise CanonicalProjectionError(f"{field} must be a non-empty string")
    return value.strip()


def project_for_mrl(
    canonical: Mapping[str, Any],
    *,
    external_view: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """Return the MRL-side presentation of an entity.

    The canonical identity controls the visible MRL name/product/history.
    Any external identity is carried only under ``source_metadata``.
    """
    canonical_name = _require_text(canonical.get("canonical_name"), "canonical_name")
    canonical_product = _require_text(
        canonical.get("canonical_product", canonical_name), "canonical_product"
    )

    result: Dict[str, Any] = {
        "display_domain": "MRL",
        "display_name": canonical_name,
        "display_product": canonical_product,
        "canonical_name": canonical_name,
        "canonical_product": canonical_product,
        "origin_signature": canonical.get("origin_signature", ORIGIN_SIGNATURE),
        "canonical_history": deepcopy(canonical.get("canonical_history", [])),
        "source_metadata": {},
        "projection_policy": "external_view_never_overrides_mrl_canonical",
    }

    if external_view:
        result["source_metadata"] = {
            "external_name": external_view.get("external_name"),
            "external_product": external_view.get("external_product"),
            "external_origin": external_view.get("external_origin"),
            "source_ref": external_view.get("source_ref"),
            "source_version": external_view.get("source_version"),
        }

    return result


def stage_external_write(
    current_canonical: Mapping[str, Any],
    external_change: Mapping[str, Any],
) -> Dict[str, Any]:
    """Stage an external change without mutating canonical state.

    This is deliberately additive. The returned ``shadow_state`` records what
    the external side requested, while ``canonical_snapshot`` is preserved
    byte-for-byte at the object level via deepcopy.
    """
    return {
        "status": "PROPOSED_ONLY",
        "target": "shadow_state",
        "canonical_mutated": False,
        "canonical_snapshot": deepcopy(dict(current_canonical)),
        "proposed_external_change": deepcopy(dict(external_change)),
        "requires_validation": True,
        "requires_root_authorization": True,
    }


def validate_projection_invariants(view: Mapping[str, Any]) -> None:
    """Fail if an MRL presentation is controlled by an external alias."""
    if view.get("display_domain") != "MRL":
        raise CanonicalProjectionError("display_domain must be MRL")
    if view.get("display_name") != view.get("canonical_name"):
        raise CanonicalProjectionError("external alias attempted to override canonical_name")
    if view.get("display_product") != view.get("canonical_product"):
        raise CanonicalProjectionError("external product attempted to override canonical_product")


__all__ = [
    "CanonicalProjectionError",
    "project_for_mrl",
    "stage_external_write",
    "validate_projection_invariants",
]
