# origin_signature: MrLiouWord
# MRL_AI_SuperComputer v1.0.0 — Unified Server
# DL580 AI Supercomputer Line (port 8787)
# Combines: FlowCore Loop + FlowAgent API + ZoomEngine + ParticleEarth
# LAW-0 Compliant | origin_signature: MrLiouWord

import os, sys, json, time, hashlib, uuid
from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs

VERSION = "1.0.0"
ORIGIN = "MrLiouWord"
PORT = int(os.environ.get("MRL_PORT", 8787))

# Import subsystems
sys.path.insert(0, os.path.dirname(__file__))

try:
    from ai_fusion_core import AIParticle, FusionStack, MobiusLoop, BaseAIProvider
    from fusion_strategies import apply_strategy
    FUSION_OK = True
except ImportError:
    FUSION_OK = False

try:
    from zoom_engine import ZoomEngine, ZoomLevel
    ZOOM_OK = True
except ImportError:
    ZOOM_OK = False

try:
    from particle_earth import project_nodes
    EARTH_OK = True
except ImportError:
    EARTH_OK = False

try:
    from ai_providers import AIProviderManager
    PROVIDERS_OK = True
except ImportError:
    PROVIDERS_OK = False

# ═══════════════════════════════════════
# State
# ═══════════════════════════════════════

trace_log = []
merkle_chain = []
zoom_engine = ZoomEngine() if ZOOM_OK else None
persona_dir = os.path.join(os.path.dirname(__file__), "models")

def now_iso():
    return datetime.now(timezone.utc).isoformat()

def sha256(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, default=str).encode()).hexdigest()

def add_trace(action, data):
    entry = {"ts": now_iso(), "action": action, "hash": sha256(data)[:16]}
    trace_log.append(entry)
    prev = merkle_chain[-1]["root"] if merkle_chain else "0" * 64
    root = hashlib.sha256((prev + entry["hash"]).encode()).hexdigest()
    merkle_chain.append({"tick": len(merkle_chain), "root": root})
    return root

def json_response(handler, data, status=200):
    body = json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("X-Origin", ORIGIN)
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)

# ═══════════════════════════════════════
# FlowAgent Translate / Restore / Simulate
# ═══════════════════════════════════════

fltnz_store = {}

def flowagent_translate(text, source_type="text"):
    h = hashlib.sha256(text.encode()).hexdigest()[:16]
    fp = f"fltnz_{h}"
    result = {
        "format": "FLTNZ", "version": "1.0", "fingerprint": fp,
        "encoded": f"FLTNZ({text})",
        "structure": {"raw_length": len(text)},
        "reversible": True, "origin_signature": ORIGIN
    }
    fltnz_store[fp] = text
    add_trace("translate", {"fingerprint": fp})
    return result

def flowagent_restore(fltnz=None, fingerprint=None):
    if fingerprint and fingerprint in fltnz_store:
        return {"restored": fltnz_store[fingerprint], "source": "store", "reversibility": "100%", "origin_signature": ORIGIN}
    import re
    m = re.match(r"^FLTNZ\((.+)\)$", fltnz or "", re.DOTALL)
    if m:
        return {"restored": m.group(1), "source": "format", "reversibility": "100%", "origin_signature": ORIGIN}
    return {"restored": fltnz or "", "source": "passthrough", "origin_signature": ORIGIN}

def flowagent_simulate(question, persona="MrLiou.flpkg"):
    persona_file = os.path.join(persona_dir, persona)
    persona_loaded = os.path.exists(persona_file)
    add_trace("simulate", {"question": question[:50], "persona": persona})
    return {
        "question": question, "persona_used": persona,
        "persona_loaded": persona_loaded,
        "result": f"{persona} → {question}",
        "trace_Y": f"{persona.replace('.flpkg','')}_YES.fltnz",
        "trace_N": f"{persona.replace('.flpkg','')}_NO.fltnz",
        "pluggable": True, "origin_signature": ORIGIN
    }

# ═══════════════════════════════════════
# HTTP Handler
# ═══════════════════════════════════════

class MRLHandler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET,POST,OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type,Authorization")
        self.end_headers()

    def _read_body(self):
        length = int(self.headers.get("Content-Length", 0))
        if length:
            return json.loads(self.rfile.read(length))
        return {}

    def do_GET(self):
        path = urlparse(self.path).path
        qs = parse_qs(urlparse(self.path).query)

        if path in ("/", "/health", "/judge/health"):
            return json_response(self, {
                "ok": True, "service": "MRL_AI_SuperComputer",
                "version": VERSION, "origin_signature": ORIGIN,
                "port": PORT,
                "subsystems": {
                    "FlowCore": True, "FlowAgent_API": True,
                    "ZoomEngine": ZOOM_OK, "ParticleEarth": EARTH_OK,
                    "AI_Fusion": FUSION_OK, "AI_Providers": PROVIDERS_OK
                },
                "merkle_root": merkle_chain[-1]["root"] if merkle_chain else None,
                "trace_count": len(trace_log),
                "endpoints": {
                    "GET /health": "健康檢查 + Merkle 錨點",
                    "POST /flowagent/translate": "萬物粒子化 (text → FLTNZ)",
                    "POST /flowagent/restore": "粒子還原 (FLTNZ → text)",
                    "POST /flowagent/simulate": "人格模組推理 (.flpkg 插拔)",
                    "POST /api/project": "粒子地球投射 (ParticleEarth)",
                    "POST /api/zoom/in|out|set|expand|collapse": "ZoomEngine 縮放控制",
                    "POST /ai/fusion/execute": "AI 融合堆疊執行",
                    "POST /ai/fusion/mobius": "莫比烏斯循環融合",
                    "GET  /ai/fusion/manifests": "融合清單"
                },
                "architecture": "DL580:8787 ← CF Worker mrl-reasoning-engine ← Edge",
                "ts": now_iso()
            })

        if path == "/ai/fusion/manifests" and FUSION_OK:
            manifest_dir = os.path.join(os.path.dirname(__file__), "fusion_manifests")
            manifests = []
            if os.path.exists(manifest_dir):
                for f in os.listdir(manifest_dir):
                    if f.endswith(".json"):
                        with open(os.path.join(manifest_dir, f)) as fh:
                            manifests.append(json.load(fh))
            return json_response(self, {"ok": True, "manifests": manifests, "origin_signature": ORIGIN})

        if path == "/api/zoom/state" and ZOOM_OK:
            return json_response(self, {"ok": True, **zoom_engine.export_state(), "origin_signature": ORIGIN})

        return json_response(self, {"error": "not_found", "origin_signature": ORIGIN}, 404)

    def do_POST(self):
        path = urlparse(self.path).path
        try:
            body = self._read_body()
        except Exception as e:
            return json_response(self, {"error": str(e)}, 400)

        # ── FlowAgent Translate ──
        if path == "/flowagent/translate":
            text = body.get("text", "")
            if not text:
                return json_response(self, {"error": "text required"}, 400)
            return json_response(self, {"ok": True, **flowagent_translate(text, body.get("source_type", "text"))})

        # ── FlowAgent Restore ──
        if path == "/flowagent/restore":
            return json_response(self, {"ok": True, **flowagent_restore(body.get("fltnz"), body.get("fingerprint"))})

        # ── FlowAgent Simulate ──
        if path == "/flowagent/simulate":
            question = body.get("question", body.get("input", ""))
            persona = body.get("persona", "MrLiou.flpkg")
            if not question:
                return json_response(self, {"error": "question required"}, 400)
            return json_response(self, {"ok": True, **flowagent_simulate(question, persona)})

        # ── Particle Earth Projection ──
        if path == "/api/project" and EARTH_OK:
            nodes = body.get("nodes", [])
            if not nodes:
                return json_response(self, {"error": "nodes required"}, 400)
            opts = body.get("options", {})
            project_nodes(nodes, "/tmp/mrl_earth_out",
                          alpha=opts.get("alpha", 1.0),
                          threshold=opts.get("threshold", 10.0))
            # Read outputs
            out = {}
            for f in ["projected_nodes.json", "edges.json", "reflect_view.json", "run_meta.json"]:
                fp = os.path.join("/tmp/mrl_earth_out", f)
                if os.path.exists(fp):
                    with open(fp) as fh:
                        out[f.replace(".json", "")] = json.load(fh)
            add_trace("project", {"node_count": len(nodes)})
            return json_response(self, {"ok": True, **out, "origin_signature": ORIGIN})

        # ── ZoomEngine ──
        if path.startswith("/api/zoom/") and ZOOM_OK:
            action = path.split("/")[-1]
            if action == "in":
                zoom_engine.zoom_in()
                return json_response(self, {"ok": True, **zoom_engine.export_state(), "origin_signature": ORIGIN})
            elif action == "out":
                zoom_engine.zoom_out()
                return json_response(self, {"ok": True, **zoom_engine.export_state(), "origin_signature": ORIGIN})
            elif action == "set":
                level = body.get("level", "core")
                zoom_engine.set_zoom_level(ZoomLevel(level))
                return json_response(self, {"ok": True, **zoom_engine.export_state(), "origin_signature": ORIGIN})
            elif action == "expand":
                pid = body.get("particle_id", "")
                result = zoom_engine.expand(pid, body.get("N", 2), body.get("eta", 1.0))
                return json_response(self, {"ok": True, "expanded": len(result), "origin_signature": ORIGIN})
            elif action == "add":
                pid = body.get("id", "")
                level = ZoomLevel(body.get("level", "core"))
                zoom_engine.add_particle(pid, level, body.get("content", ""))
                return json_response(self, {"ok": True, "particle_id": pid, "origin_signature": ORIGIN})

        # ── AI Fusion Execute ──
        if path == "/ai/fusion/execute" and FUSION_OK:
            prompt = body.get("prompt", "")
            manifest_name = body.get("manifest", "sequential_refine")
            add_trace("fusion_execute", {"manifest": manifest_name})
            return json_response(self, {
                "ok": True, "prompt": prompt, "manifest": manifest_name,
                "result": f"[Fusion:{manifest_name}] {prompt[:100]}",
                "note": "Connect AI provider keys for live execution",
                "origin_signature": ORIGIN
            })

        # ── AI Fusion Möbius ──
        if path == "/ai/fusion/mobius" and FUSION_OK:
            prompt = body.get("prompt", "")
            max_cycles = body.get("max_cycles", 3)
            add_trace("fusion_mobius", {"max_cycles": max_cycles})
            return json_response(self, {
                "ok": True, "prompt": prompt, "mode": "mobius_loop",
                "max_cycles": max_cycles,
                "result": f"[Möbius:{max_cycles}cycles] {prompt[:100]}",
                "note": "Connect AI provider keys for live execution",
                "origin_signature": ORIGIN
            })

        # ── Vault Write (from original FlowCore) ──
        if path == "/vault/write_text":
            fpath = body.get("path", "")
            text = body.get("text", "")
            if not fpath or not text:
                return json_response(self, {"error": "path and text required"}, 400)
            full = os.path.join(os.path.dirname(__file__), fpath)
            os.makedirs(os.path.dirname(full), exist_ok=True)
            with open(full, "w", encoding="utf-8") as f:
                f.write(text)
            root = add_trace("vault_write", {"path": fpath, "size": len(text)})
            return json_response(self, {"ok": True, "path": fpath, "merkle_root": root, "origin_signature": ORIGIN})

        return json_response(self, {"error": "not_found", "origin_signature": ORIGIN}, 404)


# ═══════════════════════════════════════
# Main
# ═══════════════════════════════════════

def main():
    add_trace("system.boot", {"version": VERSION, "origin": ORIGIN})
    print(f"""
# origin_signature: MrLiouWord
# ═══════════════════════════════════════════════════════
#   MRL_AI_SuperComputer v{VERSION}
#   DL580 AI Supercomputer Line — Port {PORT}
#   LAW-0: origin_signature = MrLiouWord
#
#   Subsystems:
#     FlowCore Loop    ✅
#     FlowAgent API    ✅ (translate/restore/simulate)
#     ZoomEngine       {'✅' if ZOOM_OK else '❌ (zoom_engine.py not found)'}
#     ParticleEarth    {'✅' if EARTH_OK else '❌ (particle_earth.py not found)'}
#     AI Fusion        {'✅' if FUSION_OK else '❌ (ai_fusion_core.py not found)'}
#     AI Providers     {'✅' if PROVIDERS_OK else '⚠️ (set API keys in config/)'}
# ═══════════════════════════════════════════════════════
    """)
    server = ThreadingHTTPServer(("0.0.0.0", PORT), MRLHandler)
    print(f"🚀 Listening on http://0.0.0.0:{PORT}")
    print(f"   Health: http://127.0.0.1:{PORT}/health")
    print(f"   Edge:   https://reasoning.mrliouword.com → bridge → :{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 MRL_AI_SuperComputer shutdown")
        server.shutdown()

if __name__ == "__main__":
    main()
