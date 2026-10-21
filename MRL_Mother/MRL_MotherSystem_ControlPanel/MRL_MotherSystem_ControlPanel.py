# -*- coding: utf-8 -*-
"""
MRL_MotherSystem_ControlPanel.py — 母體聚集點空間面板(神經線聚合 + 映射現狀)
origin_signature: MrLiouWord
完成 Manus 未竟任務:在已銜接的神經位置建聚集點面板,映射各區域現狀,寫入即同步。
純 stdlib,跑在 DL580,聚合本機所有母體神經線服務。
"""
import json, os, urllib.request, http.server, socketserver, datetime, threading

ORIGIN = "MrLiouWord"
PANEL_PORT = int(os.environ.get("MRL_PANEL_PORT", "7950"))
# 安全預設:只綁 127.0.0.1(本機);DL580 實機要對外時設 MRL_PANEL_BIND=0.0.0.0 才 opt-in。
PANEL_BIND = os.environ.get("MRL_PANEL_BIND", "127.0.0.1")
# 後端 x-api-key 一律由環境變數提供,不 baked 明碼;未設則拒絕呼叫後端(deny-by-default)。
BACKEND_KEY = os.environ.get("MRL_BACKEND_KEY", "")
# CORS 預設關閉;需要跨源時設 MRL_PANEL_CORS=<允許來源>(或 * 自負風險)。
PANEL_CORS = os.environ.get("MRL_PANEL_CORS", "")

# 母體神經線(區域):port -> (顯示名, health 路徑)
REGIONS = [
    (7500, "粒子推理引擎 (Qwen2.5-32B)", "/health"),
    (7700, "ASI Engine", "/health"),
    (7810, "推理引擎 ReasoningEngine", "/health"),
    (7811, "工具引擎 ToolEngine", "/health"),
    (7812, "記憶引擎 MemoryEngine", "/health"),
    (7815, "神經線 7815", "/health"),
    (7820, "神經線 7820", "/health"),
    (7900, "神經線 7900", "/health"),
    (8080, "WebConsole 8080", "/"),
    (8787, "神經線 8787", "/health"),
    (8788, "粒子快取 ParticleCache", "/"),
]

def probe(port, path):
    url = "http://127.0.0.1:%d%s" % (port, path)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "MRL-Panel/1.0"})
        with urllib.request.urlopen(req, timeout=4) as r:
            raw = r.read(4000).decode("utf-8", "replace")
        try:
            data = json.loads(raw)
        except Exception:
            data = {"raw": raw[:200]}
        return {"port": port, "alive": True, "status": data.get("status") or data.get("service") or "ALIVE", "detail": data}
    except Exception as e:
        return {"port": port, "alive": False, "status": "DOWN", "detail": {"error": str(e)[:120]}}

def aggregate():
    nodes = []
    for port, name, path in REGIONS:
        st = probe(port, path)
        st["name"] = name
        nodes.append(st)
    alive = sum(1 for n in nodes if n["alive"])
    return {"origin_signature": ORIGIN, "panel": "MRL_MotherSystem_ControlPanel",
            "regions_total": len(nodes), "regions_alive": alive,
            "nodes": nodes, "timestamp": datetime.datetime.utcnow().isoformat() + "Z"}

def chat_real(message):
    if not BACKEND_KEY:
        raise RuntimeError("MRL_BACKEND_KEY 未設定:拒絕呼叫後端(deny-by-default,不 baked 明碼 key)")
    body = json.dumps({"message": message, "max_tokens": 256}).encode("utf-8")
    req = urllib.request.Request("http://127.0.0.1:7500/MRL_chat", data=body, method="POST",
        headers={"x-api-key": BACKEND_KEY, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=140) as r:
        return json.loads(r.read().decode("utf-8", "replace"))

PAGE = """<!doctype html><html lang=zh-Hant><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1"><title>MRL 母體聚集點空間面板</title>
<style>body{margin:0;background:#07090d;color:#e6f0ff;font-family:system-ui,'Noto Sans TC',sans-serif}
header{padding:16px 20px;border-bottom:1px solid #16324a;background:linear-gradient(180deg,#0a1622,#07090d)}
h1{margin:0;font-size:18px;color:#5fd0ff}.sig{color:#3a6a8a;font-size:12px;margin-top:4px}
.wrap{max-width:1100px;margin:0 auto;padding:18px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}
.node{background:#0e1822;border:1px solid #16324a;border-radius:12px;padding:14px;position:relative}
.node.up{border-color:#1f7a4d}.node.down{border-color:#7a2a2a;opacity:.7}
.dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:7px}
.up .dot{background:#3ad17a;box-shadow:0 0 8px #3ad17a}.down .dot{background:#d15a5a}
.nm{font-size:14px;font-weight:600}.pt{color:#6a90b0;font-size:12px;margin:4px 0}
.st{font-size:12px;color:#9fd}.det{font-size:11px;color:#5a7a9a;margin-top:6px;max-height:64px;overflow:auto;white-space:pre-wrap}
.bar{display:flex;gap:14px;align-items:center;margin:10px 0 16px}
.pill{background:#0e1822;border:1px solid #16324a;border-radius:999px;padding:5px 12px;font-size:13px}
.chat{margin-top:18px;background:#0e1822;border:1px solid #16324a;border-radius:12px;padding:14px}
textarea{width:100%;background:#07090d;color:#e6f0ff;border:1px solid #16324a;border-radius:8px;padding:9px;font:inherit}
button{background:#1f7a4d;color:#fff;border:0;border-radius:8px;padding:9px 16px;cursor:pointer;margin-top:8px}
pre{background:#07090d;border:1px solid #16324a;border-radius:8px;padding:10px;white-space:pre-wrap;font-size:13px;max-height:240px;overflow:auto}</style></head>
<body><header><h1>🌌 MRL 母體聚集點空間面板</h1><div class=sig>origin_signature=MrLiouWord ｜ 神經線聚合 · 映射現狀 · 寫入即同步 ｜ DL580</div></header>
<div class=wrap>
<div class=bar><span class=pill id=summary>載入中…</span><span class=pill>自動刷新 5s</span></div>
<div class=grid id=grid></div>
<div class=chat><div style=font-size:14px;color:#5fd0ff;margin-bottom:8px>母體對話(真模型 Qwen2.5-32B · 埠 7500)</div>
<textarea id=msg rows=2 placeholder=對母體說…>用一句話自我介紹</textarea>
<button onclick=send()>送出</button><pre id=out></pre></div>
</div>
<script>
async function refresh(){
 const a=await (await fetch('/api/aggregate')).json();
 document.getElementById('summary').textContent='神經線 '+a.regions_alive+' / '+a.regions_total+' ALIVE';
 document.getElementById('grid').innerHTML=a.nodes.map(n=>
  `<div class="node ${n.alive?'up':'down'}"><div class=nm><span class=dot></span>${n.name}</div>
   <div class=pt>:${n.port}</div><div class=st>${n.status}</div>
   <div class=det>${JSON.stringify(n.detail).slice(0,240)}</div></div>`).join('');
}
async function send(){
 const out=document.getElementById('out');out.textContent='…';
 const r=await fetch('/api/chat',{method:'POST',headers:{'content-type':'application/json'},
   body:JSON.stringify({message:document.getElementById('msg').value})});
 const d=await r.json();out.textContent=d.response||JSON.stringify(d,null,2);
}
refresh();setInterval(refresh,5000);
</script></body></html>"""

class H(http.server.BaseHTTPRequestHandler):
    def _send(self, code, body, ctype="application/json; charset=utf-8"):
        b = body.encode("utf-8") if isinstance(body, str) else body
        self.send_response(code); self.send_header("Content-Type", ctype)
        # CORS 預設關閉;僅在 MRL_PANEL_CORS 有設時才送 header(避免對外時被任意網頁跨站呼叫)。
        if PANEL_CORS:
            self.send_header("Access-Control-Allow-Origin", PANEL_CORS)
        self.end_headers(); self.wfile.write(b)
    def log_message(self, *a): pass
    def do_GET(self):
        p = self.path.split("?")[0]
        if p in ("/", "/index.html"): return self._send(200, PAGE, "text/html; charset=utf-8")
        if p == "/health": return self._send(200, json.dumps({"ok": True, "service": "MRL_MotherSystem_ControlPanel", "origin_signature": ORIGIN, "port": PANEL_PORT}))
        if p == "/api/aggregate": return self._send(200, json.dumps(aggregate(), ensure_ascii=False))
        return self._send(404, json.dumps({"error": "not found"}))
    def do_POST(self):
        p = self.path.split("?")[0]
        if p == "/api/chat":
            n = int(self.headers.get("Content-Length", 0)); body = json.loads(self.rfile.read(n) or b"{}")
            try: return self._send(200, json.dumps(chat_real(body.get("message", "")), ensure_ascii=False))
            except Exception as e: return self._send(502, json.dumps({"error": str(e)}, ensure_ascii=False))
        return self._send(404, json.dumps({"error": "not found"}))

class TS(socketserver.ThreadingMixIn, http.server.HTTPServer): daemon_threads = True

if __name__ == "__main__":
    print("MRL_MotherSystem_ControlPanel on %s:%d origin=%s" % (PANEL_BIND, PANEL_PORT, ORIGIN))
    TS((PANEL_BIND, PANEL_PORT), H).serve_forever()
