import os, json, time, uuid, hashlib, datetime as _dt, re
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# Import fusion system
try:
    from ai_fusion_core import (
        AIParticle, FusionStack, MobiusLoop, BaseAIProvider,
        load_fusion_manifest, create_stack_from_manifest
    )
    from fusion_strategies import apply_strategy
    FUSION_AVAILABLE = True
except ImportError:
    FUSION_AVAILABLE = False

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
# AI Fusion Judge Functions
# -------------------------
def judge_ai_fusion(fusion_stack, tracer, vault, prompt, manifest_name):
    """
    Execute AI fusion with full audit trail
    執行 AI 融合並完整稽核追蹤
    """
    fusion_id = fusion_stack.fusion_id
    
    # Emit pre-fusion trace
    tracer.emit("fusion_pre", {
        "fusion_id": fusion_id,
        "manifest": manifest_name,
        "mode": fusion_stack.fusion_mode,
        "prompt": prompt[:100]
    })
    
    # Execute fusion
    result = fusion_stack.execute(prompt)
    
    # Save outputs to memory
    fusion_dir = f"memory/ingest/fusion/{fusion_id}"
    _ensure_dir(fusion_dir)
    
    # Save each cycle/output
    for i, output in enumerate(result.get("outputs", [])):
        output_path = f"{fusion_dir}/output_{i}_{output.get('provider', 'unknown')}.txt"
        vault.write_text(output_path, output.get("output", ""))
    
    # Save final result
    result_path = f"{fusion_dir}/merged_result.txt"
    vault.write_text(result_path, result.get("final_result", ""))
    
    # Save full result JSON
    result_json_path = f"{fusion_dir}/fusion_result.json"
    vault.write_text(result_json_path, _json(result))
    
    # Emit post-fusion trace
    tracer.emit("fusion_post", {
        "fusion_id": fusion_id,
        "manifest": manifest_name,
        "outputs_saved": len(result.get("outputs", [])),
        "result_path": result_path
    })
    
    return result

def judge_mobius_loop(mobius, tracer, vault, prompt, max_cycles):
    """
    Execute Möbius loop with cycle tracking
    執行莫比烏斯循環並追蹤循環
    """
    loop_id = mobius.loop_id
    
    # Emit pre-loop trace
    tracer.emit("mobius_pre", {
        "loop_id": loop_id,
        "prompt": prompt[:100],
        "max_cycles": max_cycles
    })
    
    # Execute loop
    result = mobius.run(prompt, max_cycles=max_cycles)
    
    # Save cycle history
    loop_dir = f"memory/ingest/mobius/{loop_id}"
    _ensure_dir(loop_dir)
    
    # Save each cycle
    for cycle_data in result.get("cycle_history", []):
        cycle_num = cycle_data["cycle"]
        cycle_dir = f"{loop_dir}/cycle_{cycle_num}"
        _ensure_dir(cycle_dir)
        
        vault.write_text(f"{cycle_dir}/input.txt", cycle_data["input"])
        vault.write_text(f"{cycle_dir}/output.txt", cycle_data["output"])
        vault.write_text(f"{cycle_dir}/cycle_data.json", _json(cycle_data))
    
    # Save convergence report
    convergence_report = {
        "converged": result.get("converged", False),
        "total_cycles": result.get("total_cycles", 0),
        "final_output": result.get("final_output", "")
    }
    vault.write_text(f"{loop_dir}/convergence_report.json", _json(convergence_report))
    
    # Emit post-loop trace
    tracer.emit("mobius_post", {
        "loop_id": loop_id,
        "converged": result.get("converged", False),
        "cycles": result.get("total_cycles", 0)
    })
    
    return result

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
        
        # AI Fusion endpoints (GET)
        if u.path == "/ai/fusion/manifests":
            if not FUSION_AVAILABLE:
                return self._send(503, {"ok": False, "error": "Fusion system not available"})
            
            # List all fusion manifests
            manifests = []
            manifest_dir = "fusion_manifests"
            if os.path.isdir(manifest_dir):
                for fn in os.listdir(manifest_dir):
                    if fn.endswith(".manifest.json"):
                        try:
                            manifest = load_fusion_manifest(os.path.join(manifest_dir, fn))
                            manifests.append({
                                "filename": fn,
                                "name": manifest.get("fusion_name", ""),
                                "mode": manifest.get("fusion_mode", ""),
                                "description": manifest.get("description", "")
                            })
                        except:
                            pass
            return self._send(200, {"ok": True, "manifests": manifests})
        
        return self._send(404, {"ok": False})

    def do_POST(self):
        ln = int(self.headers.get("Content-Length", 0))
        data = json.loads(self.rfile.read(ln) or "{}")
        
        if self.path == "/vault/write_text":
            res, snap = judge_write_text(vault, tracer, data["path"], data["text"])
            return self._send(200, {"ok": True, "res": res, "snapshot": snap})
        
        # AI Fusion endpoints (POST)
        if self.path == "/ai/fusion/execute":
            if not FUSION_AVAILABLE:
                return self._send(503, {"ok": False, "error": "Fusion system not available"})
            
            prompt = data.get("prompt", "")
            manifest_name = data.get("manifest", "")
            
            if not prompt:
                return self._send(400, {"ok": False, "error": "prompt required"})
            
            if not manifest_name:
                return self._send(400, {"ok": False, "error": "manifest required"})
            
            # Load manifest
            manifest_path = f"fusion_manifests/{manifest_name}.manifest.json"
            if not os.path.exists(manifest_path):
                return self._send(404, {"ok": False, "error": f"Manifest '{manifest_name}' not found"})
            
            try:
                manifest = load_fusion_manifest(manifest_path)
                stack = create_stack_from_manifest(manifest)
                result = judge_ai_fusion(stack, tracer, vault, prompt, manifest_name)
                return self._send(200, {"ok": True, "result": result})
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})
        
        if self.path == "/ai/fusion/mobius":
            if not FUSION_AVAILABLE:
                return self._send(503, {"ok": False, "error": "Fusion system not available"})
            
            prompt = data.get("prompt", "")
            max_cycles = data.get("max_cycles", 5)
            convergence_threshold = data.get("convergence_threshold", 0.9)
            manifest_name = data.get("manifest", "mobius_evolve")
            
            if not prompt:
                return self._send(400, {"ok": False, "error": "prompt required"})
            
            # Load manifest for Möbius loop
            manifest_path = f"fusion_manifests/{manifest_name}.manifest.json"
            if not os.path.exists(manifest_path):
                return self._send(404, {"ok": False, "error": f"Manifest '{manifest_name}' not found"})
            
            try:
                manifest = load_fusion_manifest(manifest_path)
                stack = create_stack_from_manifest(manifest)
                
                # Get transform prompt from manifest
                transform_prompt = manifest.get("transform_prompt", "Improve and expand: {output}")
                
                mobius = MobiusLoop(stack)
                result = judge_mobius_loop(mobius, tracer, vault, prompt, max_cycles)
                return self._send(200, {"ok": True, "result": result})
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})
        
        if self.path == "/ai/fusion/custom":
            if not FUSION_AVAILABLE:
                return self._send(503, {"ok": False, "error": "Fusion system not available"})
            
            prompt = data.get("prompt", "")
            mode = data.get("mode", "sequential")
            particles_config = data.get("particles", [])
            
            if not prompt:
                return self._send(400, {"ok": False, "error": "prompt required"})
            
            if not particles_config:
                return self._send(400, {"ok": False, "error": "particles required"})
            
            try:
                # Create custom stack
                stack = FusionStack()
                stack.set_mode(mode)
                
                for particle_config in particles_config:
                    provider_name = particle_config.get("provider", "mock")
                    model = particle_config.get("model", "default")
                    weight = particle_config.get("weight", 1.0)
                    role = particle_config.get("role", "")
                    
                    provider = BaseAIProvider(provider_name, model)
                    particle = AIParticle(provider, weight=weight, role=role)
                    stack.add_particle(particle)
                
                result = judge_ai_fusion(stack, tracer, vault, prompt, "custom")
                return self._send(200, {"ok": True, "result": result})
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})
        
        return self._send(404, {"ok": False})

# -------------------------
# Serve
# -------------------------
if __name__ == "__main__":
    tracer = Tracer()
    vault = Vault(ROOT)
    _ensure_dir("memory/ingest/raw")
    _ensure_dir("memory/ingest/fusion")
    _ensure_dir("memory/ingest/mobius")
    _ensure_dir("memory/derived/l1")
    _ensure_dir("memory/snapshot")
    _ensure_dir("memory/domain/mobius_cycles")
    
    fusion_status = "enabled" if FUSION_AVAILABLE else "disabled"
    print(f"AI SuperComputer running on http://127.0.0.1:8787")
    print(f"Fusion System: {fusion_status}")
    
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
