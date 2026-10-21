from fastapi.testclient import TestClient

from main import CANONICAL_ID, ORIGIN_SIGNATURE, app


client = TestClient(app)


def test_health_preserves_identity_and_boundary() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.headers["X-MRL-Origin"] == ORIGIN_SIGNATURE
    assert response.headers["X-MRL-Canonical-ID"] == CANONICAL_ID
    assert response.headers["Cache-Control"] == "no-store"
    assert response.json()["exposure_boundary"] == "PUBLIC_METADATA_ONLY"


def test_product_does_not_claim_hosted_byoh_runtime() -> None:
    payload = client.get("/v1/product").json()
    assert payload["origin_signature"] == ORIGIN_SIGNATURE
    assert payload["execution_boundary"] == "CUSTOMER_CONTROLLED_BYOH_NODE"
    assert payload["public_managed_runtime_included"] is False
    assert payload["source"]["merged_pr"] == 638


def test_closure_does_not_overstate_transaction_readiness() -> None:
    payload = client.get("/v1/closure").json()
    assert payload["first_realized_revenue"] == "NOT_ASSERTED"
    assert payload["byoh_customer_acceptance"] == "REQUIRED_PER_ORDER"
    assert payload["payment_collection"] == "REQUIRED_PER_ORDER"
