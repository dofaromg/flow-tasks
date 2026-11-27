"""Compatibility exports for the canonical BYOH hardware admission gate."""

from MRL_Products.MRL_APIWorks_BYOH_Deployment_Product_v1.scripts import (
    MRL_hardware_admission_v1 as _gate,
)

AdmissionError = _gate.AdmissionError
DEFAULT_MATRIX = _gate.MATRIX
admit = _gate.evaluate
artifact_digest = _gate.artifact_digest
load_matrix = _gate.load_matrix
require_admission = _gate.require_admission
verify_artifact_bytes = _gate.verify_artifact_bytes


def main(argv=None):
    """Run the canonical gate CLI."""
    return _gate.main(argv)


if __name__ == "__main__":
    raise SystemExit(main())
