import os, json, time, uuid, hashlib, datetime as _dt, re, threading, sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

# ── Product naming ──────────────────────────────────────────────────────────
try:
    _repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _repo_root not in sys.path:
        sys.path.insert(0, _repo_root)
    from flowcore_naming import (  # type: ignore[import]
        event_name as _event_name,
        health_metadata as _health_metadata,
        server_banner as _server_banner,
    )
    _NAMING_AVAILABLE = True
except ImportError:
    _NAMING_AVAILABLE = False

    def _event_name(component: str, action: str) -> str:  # type: ignore[misc]
        return f"mrliou.flowcore.{component}.{action}"

    def _health_metadata(component: str = "runtime"):  # type: ignore[misc]
        return {}

    def _server_banner(component: str = "runtime", version=None) -> str:  # type: ignore[misc]
        return "AI SuperComputer running"
# ────────────────────────────────────────────────────────────────────────────

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

# Import AI providers
try:
    from ai_providers import AIProviderManager
    AI_PROVIDERS_AVAILABLE = True
except ImportError:
    AI_PROVIDERS_AVAILABLE = False
    print("Warning: AI providers not available. Install ai_providers.py to enable AI features.")

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
        self._lock = threading.Lock()  # Thread safety for concurrent access

    def _load_state(self):
        if os.path.exists(self.state_path):
            return json.load(open(self.state_path))
        return {"tick": 0, "merkle_root": "0"*64, "rid": uuid.uuid4().hex}

    def emit(self, event, payload):
        # Thread-safe emission with lock to prevent race conditions
        with self._lock:
            self._state["tick"] += 1
            # Produce a product-namespaced event label for machine-readable outputs.
            # Convention: event names follow the pattern "component_action" where
            # component and action are separated by the FIRST underscore only.
            # Examples:
            #   "judge_health"        -> component="judge",   action="health"
            #   "judge_ai_precomplete"-> component="judge",   action="ai_precomplete"
            #   "fusion_pre"          -> component="fusion",  action="pre"
            # For event names without an underscore the whole name becomes the
            # action under the "flowcore" component.
            # The original short 'event' value is always preserved unchanged so
            # existing consumers are unaffected.
            if "_" in event:
                component, action = event.split("_", 1)
            else:
                component, action = "flowcore", event
            ns_event = _event_name(component, action)
            rec = {
                "rid": self._state["rid"],
                "tick": self._state["tick"],
                "event": event,
                "ns_event": ns_event,
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

def judge_ai_complete(manager, tracer, vault, prompt, provider_name=None, options=None):
    """AI completion with Judge Loop pattern / AI 完成與裁決循環模式"""
    options = options or {}
    request_id = uuid.uuid4().hex
    
    # 1. Emit pre-completion trace
    tracer.emit("judge_ai_precomplete", {
        "request_id": request_id,
        "provider": provider_name or "default",
        "prompt_sha256": _sha256_bytes(prompt.encode()),
        "prompt_length": len(prompt)
    })
    
    try:
        # 2. Call AI provider with fallback
        result = manager.complete_with_fallback(prompt, provider_name, **options)
        
        # 3. Save response to memory/ingest/ai_responses/
        _ensure_dir("memory/ingest/ai_responses")
        ts = _dt.datetime.utcnow().strftime("%Y%m%d%H%M%S")
        response_path = f"memory/ingest/ai_responses/{ts}_{request_id}.json"
        
        # Create snapshot if file exists (for overwrite protection)
        snap = None
        if os.path.exists(os.path.join(vault.root, response_path)):
            prev = vault.read_text(response_path)
            snap_path = f"memory/snapshot/{_snapshot_name(response_path)}"
            vault.write_text(snap_path, prev["text"])
            snap = {"src": response_path, "snapshot": snap_path, "sha256": prev["sha256"]}
        
        # 4. Save response
        response_data = {
            "request_id": request_id,
            "prompt": prompt,
            "result": result,
            "timestamp": now_iso()
        }
        vault.write_text(response_path, _json(response_data))
        
        # 5. Track costs
        usage = result.get("usage", {})
        cost_data = _calculate_cost(result.get("provider"), result.get("model"), usage)
        _log_ai_cost(cost_data)
        
        # 6. Emit post-completion trace with cost tracking
        tracer.emit("judge_ai_postcomplete", {
            "request_id": request_id,
            "provider": result.get("provider"),
            "model": result.get("model"),
            "response_path": response_path,
            "response_sha256": _sha256_bytes(result.get("content", "").encode()),
            "usage": usage,
            "cost": cost_data,
            "fallback_used": result.get("fallback_used", False),
            "snapshot": snap
        })
        
        # 7. Return result with Merkle proof
        return {
            "ok": True,
            "request_id": request_id,
            "content": result.get("content"),
            "provider": result.get("provider"),
            "model": result.get("model"),
            "usage": usage,
            "cost": cost_data,
            "response_path": response_path,
            "merkle_root": tracer._state["merkle_root"]
        }
        
    except Exception as e:
        # Emit error trace
        tracer.emit("judge_ai_error", {
            "request_id": request_id,
            "error": str(e)
        })
        raise

def _calculate_cost(provider, model, usage):
    """Calculate cost based on provider pricing / 根據提供商定價計算費用"""
    # Simple cost calculation - can be enhanced with actual pricing
    pricing = {
        "openai": {
            "gpt-4": {"input": 0.03, "output": 0.06},  # per 1K tokens
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002}
        },
        "claude": {
            "claude-3-opus-20240229": {"input": 0.015, "output": 0.075},
            "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015}
        }
    }
    
    cost = 0.0
    input_tokens = usage.get("prompt_tokens", 0) or usage.get("input_tokens", 0) or usage.get("prompt_eval_count", 0)
    output_tokens = usage.get("completion_tokens", 0) or usage.get("output_tokens", 0) or usage.get("eval_count", 0)
    
    if provider in pricing and model in pricing[provider]:
        prices = pricing[provider][model]
        cost = (input_tokens / 1000 * prices["input"]) + (output_tokens / 1000 * prices["output"])
    
    return {
        "provider": provider,
        "model": model,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": input_tokens + output_tokens,
        "estimated_cost_usd": round(cost, 6)
    }

# Thread-safe lock for ai_costs.jsonl writes
_ai_cost_lock = threading.Lock()

def _log_ai_cost(cost_data):
    """Log AI costs to jsonl file / 記錄 AI 費用到 jsonl 檔案"""
    _ensure_dir("log")
    log_entry = {
        "timestamp": now_iso(),
        **cost_data
    }
    # Thread-safe file write to prevent interleaved writes
    with _ai_cost_lock:
        with open("log/ai_costs.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

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
            resp = {"ok": True, "anchor": rec["merkle_root"]}
            resp.update(_health_metadata("ai"))
            return self._send(200, resp)
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
        if u.path == "/ai/providers":
            # List all available AI providers
            if not AI_PROVIDERS_AVAILABLE or not ai_manager:
                return self._send(503, {"ok": False, "error": "AI providers not initialized"})
            try:
                providers = ai_manager.list_providers()
                return self._send(200, {"ok": True, "providers": providers})
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})
        
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
        if self.path == "/ai/complete":
            # Synchronous AI completion
            if not AI_PROVIDERS_AVAILABLE or not ai_manager:
                return self._send(503, {"ok": False, "error": "AI providers not initialized"})
            try:
                prompt = data.get("prompt")
                if not prompt:
                    return self._send(400, {"ok": False, "error": "Missing 'prompt' field"})
                
                # Validate prompt
                if not isinstance(prompt, str):
                    return self._send(400, {"ok": False, "error": "Prompt must be a string"})
                if len(prompt) > 100000:  # 100K character limit
                    return self._send(400, {"ok": False, "error": "Prompt exceeds maximum length (100K characters)"})
                if '\x00' in prompt:  # Check for null bytes
                    return self._send(400, {"ok": False, "error": "Prompt contains invalid characters"})
                
                provider = data.get("provider")
                options = data.get("options", {})
                
                # Validate and whitelist options
                allowed_options = {"max_tokens", "temperature", "top_p", "frequency_penalty", "presence_penalty"}
                filtered_options = {k: v for k, v in options.items() if k in allowed_options}
                
                # Validate option ranges
                if "temperature" in filtered_options:
                    temp = filtered_options["temperature"]
                    if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                        return self._send(400, {"ok": False, "error": "Temperature must be between 0 and 2"})
                if "max_tokens" in filtered_options:
                    mt = filtered_options["max_tokens"]
                    if not isinstance(mt, int) or mt < 1 or mt > 32000:
                        return self._send(400, {"ok": False, "error": "max_tokens must be between 1 and 32000"})
                
                result = judge_ai_complete(ai_manager, tracer, vault, prompt, provider, filtered_options)
                return self._send(200, result)
            except Exception as e:
                return self._send(500, {"ok": False, "error": str(e)})
        if self.path == "/ai/stream":
            # Streaming AI completion (Server-Sent Events)
            if not AI_PROVIDERS_AVAILABLE or not ai_manager:
                return self._send(503, {"ok": False, "error": "AI providers not initialized"})
            try:
                prompt = data.get("prompt")
                if not prompt:
                    return self._send(400, {"ok": False, "error": "Missing 'prompt' field"})
                
                # Validate prompt
                if not isinstance(prompt, str):
                    return self._send(400, {"ok": False, "error": "Prompt must be a string"})
                if len(prompt) > 100000:  # 100K character limit
                    return self._send(400, {"ok": False, "error": "Prompt exceeds maximum length (100K characters)"})
                if '\x00' in prompt:  # Check for null bytes
                    return self._send(400, {"ok": False, "error": "Prompt contains invalid characters"})
                
                provider_name = data.get("provider")
                options = data.get("options", {})
                
                # Validate and whitelist options
                allowed_options = {"max_tokens", "temperature", "top_p", "frequency_penalty", "presence_penalty"}
                filtered_options = {k: v for k, v in options.items() if k in allowed_options}
                
                # Get provider
                # Fix: Get effective provider name for error messages
                effective_provider_name = provider_name or ai_manager.config.get("default_provider")
                provider = ai_manager.get_provider(provider_name)
                if not provider.is_available():
                    return self._send(503, {"ok": False, "error": f"Provider '{effective_provider_name}' not available"})
                
                # Send SSE headers
                self.send_response(200)
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.end_headers()
                
                # Stream response
                request_id = uuid.uuid4().hex
                tracer.emit("judge_ai_stream_start", {
                    "request_id": request_id,
                    "provider": effective_provider_name,
                    "prompt_length": len(prompt)
                })
                
                collected = []
                for chunk in provider.stream(prompt, **filtered_options):
                    collected.append(chunk)
                    # Send SSE format: "data: {json}\n\n"
                    event_data = json.dumps({"chunk": chunk})
                    self.wfile.write(f"data: {event_data}\n\n".encode())
                    self.wfile.flush()
                
                # Send done event
                full_response = "".join(collected)
                tracer.emit("judge_ai_stream_end", {
                    "request_id": request_id,
                    "provider": effective_provider_name,
                    "response_length": len(full_response),
                    "response_sha256": _sha256_bytes(full_response.encode())
                })
                
                self.wfile.write(b"data: [DONE]\n\n")
                return
                
            except Exception as e:
                # Emit error trace for audit consistency
                error_message = str(e)
                request_id = uuid.uuid4().hex
                tracer.emit("judge_ai_stream_error", {
                    "request_id": request_id,
                    "provider": data.get("provider") or ai_manager.config.get("default_provider"),
                    "error": error_message
                })
                error_event = json.dumps({"error": error_message})
                self.wfile.write(f"data: {error_event}\n\n".encode())
                self.wfile.write(b"data: [DONE]\n\n")  # Properly close the stream
                return
        
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
    _ensure_dir("memory/ingest/ai_responses")
    _ensure_dir("memory/derived/l1")
    _ensure_dir("memory/snapshot")
    
    # Initialize AI provider manager
    ai_manager = None
    if AI_PROVIDERS_AVAILABLE:
        config_path = "config/ai_providers.json"
        if os.path.exists(config_path):
            try:
                ai_manager = AIProviderManager(config_path)
                print(f"✓ AI providers initialized: {list(ai_manager.providers.keys())}")
            except Exception as e:
                print(f"⚠ Failed to initialize AI providers: {e}")
        else:
            print(f"⚠ AI config not found: {config_path}")
    
    print(_server_banner("ai"))
    print(f"Listening on http://127.0.0.1:8787")
    _ensure_dir("memory/ingest/fusion")
    _ensure_dir("memory/ingest/mobius")
    _ensure_dir("memory/derived/l1")
    _ensure_dir("memory/snapshot")
    _ensure_dir("memory/domain/mobius_cycles")
    
    fusion_status = "enabled" if FUSION_AVAILABLE else "disabled"
    print(f"Fusion System: {fusion_status}")
    
    ThreadingHTTPServer(("127.0.0.1", 8787), Handler).serve_forever()
