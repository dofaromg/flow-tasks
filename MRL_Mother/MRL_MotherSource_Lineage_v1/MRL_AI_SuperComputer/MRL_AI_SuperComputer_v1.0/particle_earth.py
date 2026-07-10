# origin_signature: MrLiouWord
# ParticleEarth — Geographic particle projection with ring/sector/cell coordinates

import hashlib
ORIGIN = "MrLiouWord"

def project_nodes(nodes):
    projected = []
    for i, n in enumerate(nodes):
        lat, lon = n.get("lat", 0), n.get("lon", 0)
        ring = int(abs(lat) / 2.5)
        sector = int(lon / 12) % 30
        cell = i % 686
        pressure = i + 1
        jump = pressure > 100
        projected.append({
            "id": n.get("id", f"n{i}"), "lat": lat, "lon": lon,
            "time": n.get("time", ""), "ring": ring, "sector": sector, "cell": cell,
            "pressure": pressure, "jump": jump, "origin_signature": ORIGIN
        })
    return projected

def compute_pressure_field(nodes):
    field = {}
    for n in nodes:
        r = n.get("ring", 0)
        field[r] = field.get(r, 0) + n.get("pressure", 1)
    return {"field": field, "total_pressure": sum(field.values()), "rings": len(field)}

def merkle_audit(projected):
    hashes = [hashlib.sha256(str(n).encode()).hexdigest()[:16] for n in projected]
    root = hashlib.sha256("".join(hashes).encode()).hexdigest()
    return {"root": root, "node_count": len(hashes), "origin_signature": ORIGIN}
