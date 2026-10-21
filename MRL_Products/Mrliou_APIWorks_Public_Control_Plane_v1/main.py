"""Public metadata-only control plane for MRL APIWorks.

This service intentionally does not expose the BYOH runtime, customer memory,
model inference, payment processing, or the private MRL mother topology.
"""

from typing import Final

from fastapi import FastAPI, Response


CANONICAL_ID: Final = "Mrliou_APIWorks_Public_Control_Plane_v1"
ORIGIN_SIGNATURE: Final = "MrLiouWord"
VERSION: Final = "1.0.0"
SOURCE_REPOSITORY: Final = "dofaromg/flow-tasks"
SOURCE_PR: Final = 638
PRODUCT_ID: Final = "MRL_APIWorks_BYOH_Deployment_Product_v1"
PRODUCT_SKU: Final = "MRL-APIWORKS-BYOH-DEPLOY-V1"

app = FastAPI(
    title="Mrliou APIWorks Public Control Plane",
    description="Public metadata and health surface for MRL APIWorks.",
    version=VERSION,
)


@app.middleware("http")
async def preserve_origin_signature(request, call_next):
    response = await call_next(request)
    response.headers["X-MRL-Origin"] = ORIGIN_SIGNATURE
    response.headers["X-MRL-Canonical-ID"] = CANONICAL_ID
    return response


@app.get("/", tags=["identity"])
def identity() -> dict[str, object]:
    return {
        "canonical_id": CANONICAL_ID,
        "origin_signature": ORIGIN_SIGNATURE,
        "version": VERSION,
        "surface": "PUBLIC_METADATA_ONLY",
        "links": {
            "health": "/health",
            "product": "/v1/product",
            "closure": "/v1/closure",
            "openapi": "/openapi.json",
        },
    }


@app.get("/health", tags=["operations"])
def health(response: Response) -> dict[str, object]:
    response.headers["Cache-Control"] = "no-store"
    return {
        "ok": True,
        "service": CANONICAL_ID,
        "version": VERSION,
        "origin_signature": ORIGIN_SIGNATURE,
        "exposure_boundary": "PUBLIC_METADATA_ONLY",
    }


@app.get("/v1/product", tags=["commercial"])
def product() -> dict[str, object]:
    return {
        "canonical_id": PRODUCT_ID,
        "sku": PRODUCT_SKU,
        "origin_signature": ORIGIN_SIGNATURE,
        "offering_type": "SOFTWARE_DEPLOYMENT_AND_ACCEPTANCE_SERVICE",
        "execution_boundary": "CUSTOMER_CONTROLLED_BYOH_NODE",
        "public_managed_runtime_included": False,
        "source": {
            "repository": SOURCE_REPOSITORY,
            "merged_pr": SOURCE_PR,
        },
    }


@app.get("/v1/closure", tags=["commercial"])
def closure() -> dict[str, object]:
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "public_surface": "HEALTH_AND_PRODUCT_METADATA",
        "byoh_customer_acceptance": "REQUIRED_PER_ORDER",
        "legal_order_form": "REQUIRED_PER_ORDER",
        "payment_collection": "REQUIRED_PER_ORDER",
        "first_realized_revenue": "NOT_ASSERTED",
        "interpretation": (
            "A healthy public control plane proves public service availability only; "
            "it does not prove BYOH customer acceptance or a realized transaction."
        ),
    }
