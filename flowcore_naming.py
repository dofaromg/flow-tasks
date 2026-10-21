"""
flowcore_naming.py
==================
MrLiou FlowCore — Centralized Product Naming Model
粒子語言核心系統 — 統一產品命名模組

This module is the single source of truth for all product identity values
used across the FlowCore runtime, API, CLI, trace metadata, and index outputs.

Treat this file as a product-level constant registry — the way mainstream
products (e.g. Apple, Stripe, Vercel) embed their brand/version identity
directly into their SDKs and runtimes rather than scattering ad-hoc strings
throughout the codebase.

Usage:
    from flowcore_naming import PRODUCT, event_name, server_banner, index_metadata

Origin signature: MrLiouWord
"""

from __future__ import annotations

from typing import Dict

try:
    from typing import TypedDict

    class _ProductInfo(TypedDict):
        vendor: str
        product: str
        line: str
        component: Dict[str, str]
        full_name: str
        slug: str
        namespace: str
        version: str
        origin_signature: str
        description_en: str
        description_zh: str

except ImportError:
    _ProductInfo = None  # type: ignore[assignment,misc]

# ---------------------------------------------------------------------------
# Component registry — typed separately so callers get precise dict typing
# ---------------------------------------------------------------------------

#: Canonical component names used in HTTP headers, banners, and trace labels.
COMPONENTS: Dict[str, str] = {
    "runtime": "FlowCore.Runtime",
    "vault": "FlowCore.Vault",
    "trace": "FlowCore.Trace",
    "index": "FlowCore.Index",
    "loop": "FlowCore.Loop",
    "ai": "FlowCore.AI",
    "web": "FlowCore.Web",
}

# ---------------------------------------------------------------------------
# Core product identity constants
# ---------------------------------------------------------------------------

PRODUCT: "_ProductInfo" = {  # type: ignore[assignment]
    # Brand / vendor
    "vendor": "MrLiou",
    "product": "FlowCore",
    "line": "ParticleRuntime",

    # Component registry reference (canonical names used in headers / trace / labels)
    "component": COMPONENTS,

    # Full display name
    "full_name": "MrLiou FlowCore ParticleRuntime",

    # URL / identifier slug  (e.g. for HTTP User-Agent / X-Product headers)
    "slug": "mrliou-flowcore",

    # Dot-separated namespace used in event names and schema keys
    "namespace": "mrliou.flowcore",

    # Semantic version (update on releases)
    "version": "1.0.0",

    # Identity marker preserved from the original MrLiouWord system
    "origin_signature": "MrLiouWord",

    # Human-readable descriptions
    "description_en": "Particle Language Core Runtime",
    "description_zh": "粒子語言核心系統",
}


# ---------------------------------------------------------------------------
# Helper: event / operation naming
# ---------------------------------------------------------------------------

def event_name(component: str, action: str) -> str:
    """Return a dot-separated, product-namespaced event name.

    Follows the convention: ``<namespace>.<component>.<action>``

    Examples::

        event_name("vault", "write")   -> "mrliou.flowcore.vault.write"
        event_name("trace", "emit")    -> "mrliou.flowcore.trace.emit"
        event_name("index", "compute") -> "mrliou.flowcore.index.compute"

    The short plain-text name is still accepted everywhere for backward
    compatibility; this namespaced form appears in emitted metadata and
    structured outputs to make the product identity machine-readable.
    """
    ns: str = str(PRODUCT["namespace"])
    return f"{ns}.{component}.{action}"


# ---------------------------------------------------------------------------
# Helper: server / HTTP labeling
# ---------------------------------------------------------------------------

def server_version_header(component: str = "runtime") -> str:
    """Return a value suitable for the HTTP ``Server:`` header.

    Format: ``<ComponentName>/<version>``

    Example::

        server_version_header("runtime")  -> "FlowCore.Runtime/1.0.0"
        server_version_header("ai")       -> "FlowCore.AI/1.0.0"
    """
    comp = COMPONENTS.get(component, component)
    version = str(PRODUCT["version"])
    return f"{comp}/{version}"


def server_banner(component: str = "runtime", version: str | None = None) -> str:
    """Return a one-line startup banner string for console output.

    Args:
        component: A key from :data:`COMPONENTS` (e.g. ``"runtime"``, ``"ai"``).
        version: An optional override for the version segment.  Only use this
            for pre-release or build-specific labels (e.g. ``"1.1.0-beta"``).
            Leave as ``None`` in production to ensure consistent version
            reporting from the :data:`PRODUCT` constant.

    Example::

        server_banner("runtime") ->
            "MrLiou FlowCore ParticleRuntime [FlowCore.Runtime] v1.0.0 — MrLiouWord"
    """
    comp = COMPONENTS.get(component, component)
    v = version or str(PRODUCT["version"])
    full = str(PRODUCT["full_name"])
    sig = str(PRODUCT["origin_signature"])
    return f"{full} [{comp}] v{v} — {sig}"


# ---------------------------------------------------------------------------
# Helper: structured metadata blocks for index / health / trace outputs
# ---------------------------------------------------------------------------

def index_metadata() -> Dict[str, str]:
    """Return a product metadata dict for embedding in index/manifest outputs.

    This block is included in any artifact manifest so that downstream
    tooling can identify which product/version generated the index.
    """
    return {
        "product": str(PRODUCT["full_name"]),
        "vendor": str(PRODUCT["vendor"]),
        "namespace": str(PRODUCT["namespace"]),
        "version": str(PRODUCT["version"]),
        "origin_signature": str(PRODUCT["origin_signature"]),
        "slug": str(PRODUCT["slug"]),
    }


def health_metadata(component: str = "runtime") -> Dict[str, str]:
    """Return a product metadata dict for health-check API responses.

    This allows clients to confirm they are talking to the expected
    product component and version.
    """
    return {
        "product": str(PRODUCT["full_name"]),
        "component": COMPONENTS.get(component, component),
        "version": str(PRODUCT["version"]),
        "origin_signature": str(PRODUCT["origin_signature"]),
    }


def cli_description(component: str = "runtime") -> str:
    """Return a formatted CLI description string for argparse help text."""
    comp = COMPONENTS.get(component, component)
    full = str(PRODUCT["full_name"])
    desc_en = str(PRODUCT["description_en"])
    desc_zh = str(PRODUCT["description_zh"])
    v = str(PRODUCT["version"])
    return f"{full} [{comp}] v{v} — {desc_en} / {desc_zh}"
