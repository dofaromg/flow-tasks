"""
orchestrator core — MRL multi-step pipeline (pure, zero-dependency).
origin_signature: MrLiouWord

run_pipeline takes a compute function by injection, so it is fully testable
in-process (with module-a's core) and equally works over HTTP in production.
Replaces the previous "GET module-a/info and echo" shell with a real pipeline:
validate -> compute -> near-duplicate dedup -> aggregate, with a step trace.
"""


def hamming_hex(a_hex: str, b_hex: str) -> int:
    """Hamming distance between two hex-encoded fingerprints."""
    return bin(int(a_hex, 16) ^ int(b_hex, 16)).count("1")


def run_pipeline(payload, compute_fn) -> dict:
    if not isinstance(payload, dict):
        raise ValueError("payload_must_be_object")
    items = payload.get("items")
    if not isinstance(items, list) or not items:
        raise ValueError("items_required_nonempty")
    if len(items) > 1000:
        raise ValueError("too_many_items")

    trace = [{"step": "validate", "ok": True, "count": len(items)}]

    results = [compute_fn(text) for text in items]
    trace.append({"step": "compute", "ok": True, "processed": len(results)})

    # Near-duplicate dedup via SimHash Hamming distance.
    threshold = int(payload.get("dedup_threshold", 3))
    unique = []
    for r in results:
        if all(hamming_hex(r["simhash64"], u["simhash64"]) > threshold for u in unique):
            unique.append(r)
    trace.append({"step": "dedup", "ok": True, "threshold": threshold, "unique": len(unique)})

    total_tokens = sum(r["token_count"] for r in results)
    avg_score = round(sum(r["particle_score"] for r in results) / len(results), 6)
    trace.append({"step": "aggregate", "ok": True})

    return {
        "orchestrator": "success",
        "summary": {
            "items": len(items),
            "total_tokens": total_tokens,
            "unique_particles": len(unique),
            "avg_particle_score": avg_score,
        },
        "results": results,
        "trace": trace,
        "origin_signature": "MrLiouWord",
    }
