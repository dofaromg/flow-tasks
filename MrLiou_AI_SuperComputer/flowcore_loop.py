import os, json, time, uuid, hashlib, datetime as _dt, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

ROOT = os.getcwd()

# -------------------------
# Utilities
# -------------------------
def now_iso():
    return _dt.datetime.utcnow().isoformat() + "Z"

def _sha256_bytes(b: bytes):
    return hashlib.sha256(b).hexdigest()

def _ensure_dir(path):
    os.makedirs(path, exist_ok=True)

def _snapshot_name(src_path: str):
    base = os.path.basename(src_path.replace("\\", "/"))
    ts = _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
    return f"{ts}_{base}"

def _json(x):
    return json.dumps(x, ensure_ascii=False, indent=2)

# -------------------------
# Trace (cycle anchor)
# -------------------------
class Tracer:
    def __init__(self):
        _ensure_dir("log")
        self.path = "log/trace.jsonl"
        self.state_path = "log/trace_state.json"
        self._state = self._load_state()
        self.rid = self._state.get("rid") or uuid.uuid4().hex

    def _load_state(self):
        if os.path.exists(self.state_path):
            return json.load(open(self.state_path))
        return {"tick": 0, "merkle_root": "0"*64, "rid": uuid.uuid4().hex}

    def emit(self, event, payload):
        self._state["tick"] += 1
        rec = {
            "rid": self._state["rid"],
            "tick": self._state["tick"],
            "event": event,
            "ts": now_iso(),
            "payload": payload
        }
        raw = json.dumps(rec, sort_keys=True).encode()
        leaf = hashlib.sha256(raw).hexdigest()
        combo = (self._state["merkle_root"] + leaf).encode()
        self._state["merkle_root"] = hashlib.sha256(combo).hexdigest()
        rec["merkle_root"] = self._state["merkle_root"]
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        json.dump(self._state, open(self.state_path, "w"))
        return rec

# -------------------------
# Vault
# -------------------------
class Vault:
    def __init__(self, root):
        self.root = root

    def _full(self, p):
        return os.path.join(self.root, p)

    def read_text(self, p, max_bytes=256_000):
        fp = self._full(p)
        with open(fp, "r", encoding="utf-8", errors="ignore") as f:
            data = f.read(max_bytes)
        return {
            "text": data,
            "sha256": _sha256_bytes(data.encode()),
            "truncated": len(data.encode()) >= max_bytes
        }

    def write_text(self, p, text, overwrite=True):
        fp = self._full(p)
        _ensure_dir(os.path.dirname(fp))
        if (not overwrite) and os.path.exists(fp):
            raise RuntimeError("exists")
        with open(fp, "w", encoding="utf-8") as f:
            f.write(text)
        return {"sha256": _sha256_bytes(text.encode()), "size": len(text.encode())}

# -------------------------
# Judge Loop (cycle return)
# -------------------------
def judge_write_text(vault, tracer, path, text):
    snap = None
    full = os.path.join(vault.root, path)
    if os.path.exists(full):
        prev = vault.read_text(path)
        _ensure_dir("memory/snapshot")
        snap_path = f"memory/snapshot/{_snapshot_name(path)}"
        vault.write_text(snap_path, prev["text"])
        snap = {"src": path, "snapshot": snap_path, "sha256": prev["sha256"]}
    tracer.emit("judge_prewrite", {"path": path, "snapshot": snap})
    res = vault.write_text(path, text)
    tracer.emit("judge_postwrite", {"path": path, "sha256": res["sha256"], "snapshot": snap})
    return res, snap

# -------------------------
# L1 Derived (low resolution)
# -------------------------
def l1_tokens(s):
    s = re.sub(r"[^a-z0-9_\\s]+", " ", s.lower())
    return [t for t in s.split() if t][:256]

def l1_build(vault, src):
    data = vault.read_text(src)
    toks = l1_tokens(data["text"])
    sig = _sha256_bytes(" ".join(toks).encode())
    out = f"memory/derived/l1/{os.path.basename(src)}.l1.json"
    vault.write_text(out, _json({"src": src, "tokens": toks, "sha256": sig}))
    return {"out": out, "sha256": sig}

# -------------------------
# HTTP
# -------------------------
class Handler(BaseHTTPRequestHandler):
    def _send(self, code, obj):
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode())

    def do_GET(self):
        u = urlparse(self.path)
        qs = parse_qs(u.query)
        if u.path == "/judge/health":
            rec = tracer.emit("judge_health", {})
            return self._send(200, {"ok": True, "anchor": rec["merkle_root"]})
        if u.path == "/l1/search":
            q = qs.get("q", [""])[0]
            hits = []
            base = "memory/derived/l1"
            if os.path.isdir(base):
                for fn in os.listdir(base):
                    if not fn.endswith(".l1.json"):
                        continue
                    obj = json.load(open(os.path.join(base, fn)))
                    score = sum(1 for t in l1_tokens(q) if t in obj.get("tokens", []))
                    if score:
                        hits.append({"file": fn, "score": score})
            hits.sort(key=lambda x: x["score"], reverse=True)
            return self._send(200, {"ok": True, "hits": hits})
        return self._send(404, {"ok": False})

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(ln) or "{}")
        if self.path == "/vault/write_text":
            res, snap = judge_write_text(vault, tracer, data["path"], data["text"])
            return self._send(200, {"ok": True, "res": res, "snapshot": snap})
        return self._send(404, {"ok": False})

# -------------------------
# Serve
# -------------------------
if __name__ == "__main__":
    tracer = Tracer()
    vault = Vault(ROOT)
    _ensure_dir("memory/ingest/raw")
    _ensure_dir("memory/derived/l1")
    _ensure_dir("memory/snapshot")
    print("AI SuperComputer running on http://127.0.0.1:8787")
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
