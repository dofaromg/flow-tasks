#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flowcore_loop.py - AI Computer Runtime (MrLiouAI-compatible)
origin_signature: MrLiouWord
module_name: FlowCoreLoop
fusion_state: ai_computer_runtime_v0.2
intent: "Provide an AI-usable local computer interface: filesystem vault + trace + minimal HTTP API + CLI."
x_policy: Anti-Scaffold Law (single-file closure, no empty shells, full runnable)

v0.2 補接：4 個 Product Gateway endpoint（最小補接，不動主循環）
  POST /task/submit
  POST /result/partial
  POST /billing/confirm
  POST /result/full
"""

from __future__ import annotations

import argparse
import base64
import datetime as _dt
import hashlib
import json
import os
import pathlib
import shutil
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse, parse_qs
import requests
FSD_API_BASE = "https://directory.fsf.org/w/api.php"

def fsd_search(q: str, limit: int = 20):
    try:
        params = {"action":"query","list":"search","srsearch":q,"srlimit":str(limit),"format":"json","formatversion":"2"}
        resp = requests.get(FSD_API_BASE, params=params, timeout=10)
        resp.raise_for_status()
        return resp.json().get("query",{}).get("search",[])
    except Exception as e:
        return {"error": str(e)}

def fsd_entry(title: str):
    try:
        params = {"action":"query","prop":"revisions","titles":title,"rvprop":"content","rvslots":"main","format":"json","formatversion":"2"}
        resp = requests.get(FSD_API_BASE, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        pages = data.get("query",{}).get("pages",[])
        if not pages: return None
        page = pages[0]
        revs = page.get("revisions",[])
        if not revs: return None
        return revs[0].get("slots",{}).get("main",{}).get("content","")
    except Exception as e:
        return {"error": str(e)}

VERSION = "0.2.0"
ORIGIN_SIGNATURE = "MrLiouWord"

# ── Product Gateway memory 路徑 ─────────────────────────────────
_P_TASKS   = "memory/ingest/raw/tasks"
_P_PARTIAL = "memory/derived/partial"
_P_FULL    = "memory/artifacts/full_results"
_P_LEDGER  = "memory/ledger"

# ── Product Adaptor 函式（沿用 Vault / Tracer 模式）─────────────

def _pg_ensure_dirs(vault):
    for p in [_P_TASKS, _P_PARTIAL, _P_FULL, _P_LEDGER]:
        vault.mkdir(p)

def _pg_submit_task(vault, tracer, prompt, category, user_id, source):
    _pg_ensure_dirs(vault)
    task_id = "task_" + uuid.uuid4().hex[:12]
    raw = {"task_id":task_id,"prompt":prompt,"category":category,
           "user_id":user_id,"source":source,"status":"accepted","origin":ORIGIN_SIGNATURE}
    vault.write_text(f"{_P_TASKS}/{task_id}.json",    json.dumps(raw,     ensure_ascii=False, indent=2))
    vault.write_text(f"{_P_PARTIAL}/{task_id}.json",  json.dumps(_pg_build_partial(prompt, category), ensure_ascii=False, indent=2))
    vault.write_text(f"{_P_FULL}/{task_id}.json",     json.dumps(_pg_build_full(prompt, category, task_id), ensure_ascii=False, indent=2))
    tracer.emit("task_submit", {"task_id":task_id,"category":category,"user_id":user_id})
    return {"task_id":task_id, "partial_result":_pg_build_partial(prompt, category)}

def _pg_build_partial(prompt, category):
    if category == "product":
        return {"summary":f"問題核心：{prompt[:60]}...","breakdown":["第一版範圍需要收斂","付款入口是第一個必存節點","先有人付錢才繼續做"],"direction":"先做最小可付費入口，再從真實回饋決定下一步","_locked":True,"_hint":"付費解鎖：完整執行步驟 / 優先順序 / 補充建議"}
    return {"summary":f"問題摘要：{prompt[:60]}...","breakdown":["完整方案需解鎖"],"direction":"解鎖後取得完整執行計畫","_locked":True}

def _pg_build_full(prompt, category, task_id):
    if category == "product":
        return {"task_id":task_id,"locked":True,"title":"第一版產品執行方案","steps":["Step 1：建立最小入口頁","Step 2：接付款流程（Stripe test mode）","Step 3：付款成功後解鎖核心功能","Step 4：收到第一筆錢再決定 Step 5"],"priorities":["最優先：付款入口","其次：問題輸入 + partial","暫緩：後台 / 報表"],"supplements":["上線前驗收：/health 200、付款流程走完一次","第一版成功定義：有人真的付錢"],"warning":["範圍失控是第一版最常見的死因","先不做的事和先做的事同樣重要"],"origin":ORIGIN_SIGNATURE}
    return {"task_id":task_id,"locked":True,"title":f"{category} 方案","steps":["完整步驟需解鎖"],"priorities":[],"supplements":[],"warning":[],"origin":ORIGIN_SIGNATURE}

def _pg_write_ledger(vault, tracer, task_id, payment_id, amount, currency, status):
    paid_at = now_iso()
    ledger  = {"task_id":task_id,"payment_id":payment_id,"amount":amount,"currency":currency,"status":status,"paid_at":paid_at,"origin":ORIGIN_SIGNATURE}
    vault.write_text(f"{_P_LEDGER}/{task_id}.json", json.dumps(ledger, ensure_ascii=False, indent=2))
    try:
        full = json.loads(vault.read_text(f"{_P_FULL}/{task_id}.json")["text"])
        full["locked"] = False; full["unlocked_at"] = paid_at
        vault.write_text(f"{_P_FULL}/{task_id}.json", json.dumps(full, ensure_ascii=False, indent=2))
    except Exception:
        pass
    tracer.emit("billing_confirm", {"task_id":task_id,"payment_id":payment_id,"amount":amount,"currency":currency})
    return ledger

def _pg_is_unlocked(vault, task_id):
    try:
        return json.loads(vault.read_text(f"{_P_LEDGER}/{task_id}.json")["text"]).get("status") == "paid"
    except Exception:
        return False

# -------------------------
# Steering
# -------------------------

def _clamp01(x):
    try:
        xf = float(x)
    except Exception:
        return 0.0
    return max(0.0, min(1.0, xf))

def _profile_hash(profile):
    return _sha256_bytes(_json_dumps(profile).encode("utf-8"))

DEFAULT_STEERING_PROFILE = {"version":"steer.v1","explain_depth":0.15,"inference_scope":0.10,"deliver_priority":0.85,"guard_sensitivity":0.35}

class SteeringStore:
    def __init__(self, dir_path):
        self.dir_path = dir_path
        os.makedirs(self.dir_path, exist_ok=True)
        self.profile_path = os.path.join(self.dir_path, "steering_profile.json")
        self.drift_path   = os.path.join(self.dir_path, "drift_stats.json")

    def load_profile(self):
        if os.path.exists(self.profile_path):
            try:
                with open(self.profile_path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                p = obj.get("profile", {})
                merged = dict(DEFAULT_STEERING_PROFILE)
                for k in ("explain_depth","inference_scope","deliver_priority","guard_sensitivity"):
                    if k in p: merged[k] = _clamp01(p[k])
                merged["version"] = DEFAULT_STEERING_PROFILE["version"]
                return merged
            except Exception:
                pass
        return dict(DEFAULT_STEERING_PROFILE)

    def save_profile(self, profile, source="explicit"):
        merged = dict(DEFAULT_STEERING_PROFILE)
        for k in ("explain_depth","inference_scope","deliver_priority","guard_sensitivity"):
            if k in profile: merged[k] = _clamp01(profile[k])
        merged["version"] = DEFAULT_STEERING_PROFILE["version"]
        rec = {"updated_at":now_iso(),"source":source,"profile":merged,"profile_hash":_profile_hash(merged)}
        tmp = self.profile_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(rec, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.profile_path)
        return rec

    def load_drift(self):
        if os.path.exists(self.drift_path):
            try:
                with open(self.drift_path, "r", encoding="utf-8") as f:
                    obj = json.load(f)
                if isinstance(obj, dict): return obj
            except Exception:
                pass
        return {"updated_at":now_iso(),"counters":{"http_error":0,"permission_denied":0,"not_found":0,"internal_error":0},"recent_event_types":[]}

    def _save_drift(self, drift):
        drift["updated_at"] = now_iso()
        tmp = self.drift_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(drift, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.drift_path)

    def bump_drift(self, event_type, error_code=None):
        drift = self.load_drift()
        ctr = drift.setdefault("counters", {})
        if error_code: ctr[error_code] = int(ctr.get(error_code, 0)) + 1
        recent = drift.setdefault("recent_event_types", [])
        recent.append(event_type)
        if len(recent) > 32: recent[:] = recent[-32:]
        self._save_drift(drift)
        return drift

def preflight_router(path, method, headers, body, store):
    p = store.load_profile()
    if path.startswith("/vault/"):
        p["deliver_priority"] = max(p["deliver_priority"], 0.95)
        p["inference_scope"]  = min(p["inference_scope"],  0.05)
        p["explain_depth"]    = min(p["explain_depth"],    0.25)
    mode = (headers.get("X-Flow-Mode") or headers.get("x-flow-mode") or "").strip().lower()
    if mode == "direct":   p.update({"explain_depth":0.05,"inference_scope":0.05,"deliver_priority":0.95})
    elif mode == "deliver": p.update({"explain_depth":0.10,"inference_scope":0.05,"deliver_priority":1.00})
    elif mode == "engineer":p.update({"explain_depth":0.20,"inference_scope":0.05,"deliver_priority":0.85,"guard_sensitivity":0.25})
    elif mode == "risk":    p.update({"guard_sensitivity":0.85,"explain_depth":max(p["explain_depth"],0.35)})
    if body and isinstance(body, dict):
        if body.get("no_reason") is True: p["explain_depth"] = min(p["explain_depth"], 0.10)
        if body.get("delivery_only") is True: p.update({"deliver_priority":1.00,"inference_scope":0.0,"explain_depth":min(p["explain_depth"],0.10)})
    return p

# -------------------------
# Trace / Merkle
# -------------------------

def _sha256_bytes(b):
    return hashlib.sha256(b).hexdigest()

def _json_dumps(obj):
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",",":"))

def merkle_fold(prev_root, payload):
    p    = _json_dumps(payload).encode("utf-8")
    leaf = _sha256_bytes(p)
    combo = (prev_root + leaf).encode("utf-8")
    return _sha256_bytes(combo)

def now_iso():
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")

class Tracer:
    def __init__(self, log_dir, persona_id="PartnerPersona", rid=None):
        self.log_dir    = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.trace_path = os.path.join(self.log_dir, "trace.jsonl")
        self.state_path = os.path.join(self.log_dir, "trace_state.json")
        self.persona_id = persona_id
        self.rid        = rid or uuid.uuid4().hex[:12]
        self._state     = self._load_state()

    def _load_state(self):
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"merkle_root": "0"*64, "tick": 0}

    def _save_state(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.state_path)

    def emit(self, event_type, payload):
        self._state["tick"] += 1
        event_id = uuid.uuid4().hex
        rec = {"event_id":event_id,"rid":self.rid,"tick":self._state["tick"],"ts":now_iso(),"persona_id":self.persona_id,"origin_signature":ORIGIN_SIGNATURE,"event_type":event_type,"payload":payload}
        new_root = merkle_fold(self._state["merkle_root"], rec)
        rec["merkle_root"] = new_root
        self._state["merkle_root"] = new_root
        with open(self.trace_path, "a", encoding="utf-8") as f:
            f.write(_json_dumps(rec) + "\n")
        self._save_state()
        return rec

# -------------------------
# Vault
# -------------------------

def safe_realpath(p):
    return os.path.realpath(os.path.expanduser(p))

class Vault:
    def __init__(self, root_dir):
        self.root_dir = safe_realpath(root_dir)
        os.makedirs(self.root_dir, exist_ok=True)

    def _resolve(self, rel_or_abs):
        p = safe_realpath(rel_or_abs)
        if not p.startswith(self.root_dir.rstrip(os.sep) + os.sep) and p != self.root_dir:
            raise PermissionError(f"path_outside_vault_root: {p}")
        return p

    def list(self, subpath=".", max_items=200):
        p = self._resolve(os.path.join(self.root_dir, subpath))
        if not os.path.isdir(p): raise FileNotFoundError("not_a_directory")
        items = []
        for i, name in enumerate(sorted(os.listdir(p))):
            if i >= max_items: break
            fp = os.path.join(p, name)
            st = os.stat(fp)
            items.append({"name":name,"type":"dir" if os.path.isdir(fp) else "file","size":st.st_size,"mtime":int(st.st_mtime)})
        return {"path":os.path.relpath(p, self.root_dir),"items":items,"truncated":len(items)>=max_items}

    def read_text(self, path, max_bytes=256_000, encoding="utf-8"):
        fp = self._resolve(os.path.join(self.root_dir, path))
        if not os.path.isfile(fp): raise FileNotFoundError("not_a_file")
        with open(fp, "rb") as f: b = f.read(max_bytes+1)
        truncated = len(b) > max_bytes
        b = b[:max_bytes]
        try: text = b.decode(encoding, errors="replace")
        except Exception: text = b.decode("utf-8", errors="replace")
        return {"path":path,"text":text,"truncated":truncated,"sha256":_sha256_bytes(b)}

    def read_bytes_b64(self, path, max_bytes=2_000_000):
        fp = self._resolve(os.path.join(self.root_dir, path))
        if not os.path.isfile(fp): raise FileNotFoundError("not_a_file")
        with open(fp, "rb") as f: b = f.read(max_bytes+1)
        truncated = len(b) > max_bytes
        b = b[:max_bytes]
        return {"path":path,"b64":base64.b64encode(b).decode("ascii"),"truncated":truncated,"sha256":_sha256_bytes(b)}

    def write_text(self, path, text, encoding="utf-8", overwrite=True):
        fp = self._resolve(os.path.join(self.root_dir, path))
        os.makedirs(os.path.dirname(fp), exist_ok=True)
        if (not overwrite) and os.path.exists(fp): raise FileExistsError("exists")
        b = text.encode(encoding)
        tmp = fp + ".tmp"
        with open(tmp, "wb") as f: f.write(b)
        os.replace(tmp, fp)
        st = os.stat(fp)
        return {"path":path,"size":st.st_size,"sha256":_sha256_bytes(b)}

    def mkdir(self, path):
        fp = self._resolve(os.path.join(self.root_dir, path))
        os.makedirs(fp, exist_ok=True)
        return {"path":path,"ok":True}

    def info(self, path):
        fp = self._resolve(os.path.join(self.root_dir, path))
        if not os.path.exists(fp): raise FileNotFoundError("not_found")
        st = os.stat(fp)
        return {"path":path,"type":"dir" if os.path.isdir(fp) else "file","size":st.st_size,"mtime":int(st.st_mtime)}

# -------------------------
# HTTP API
# -------------------------

def make_handler(vault: Vault, tracer: Tracer, steering: SteeringStore):
    class Handler(BaseHTTPRequestHandler):
        server_version = "FlowCoreLoopHTTP/" + VERSION

        def _send(self, code, obj):
            body = _json_dumps(obj).encode("utf-8")
            self.send_response(code)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def _err(self, code, msg, detail=None, steering_profile=None):
            payload = {"ok":False,"error":msg,"detail":detail or {}}
            sp = steering_profile or steering.load_profile()
            steering.bump_drift("http_error", error_code=msg if msg in ("permission_denied","not_found","internal_error") else "http_error")
            tracer.emit("http_error", {"code":code,"msg":msg,"path":self.path,"detail":payload["detail"],"steering":sp,"steering_hash":_profile_hash(sp)})
            self._send(code, payload)

        def do_GET(self):
            try:
                u  = urlparse(self.path)
                qs = parse_qs(u.query)
                sp = preflight_router(u.path, "GET", dict(self.headers), None, steering)
                sp_hash = _profile_hash(sp)
                if u.path == "/health":
                    rec = tracer.emit("health", {"path":self.path,"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"version":VERSION,"merkle_root":rec["merkle_root"],"steering":sp,"steering_hash":sp_hash})
                if u.path == "/vault/list":
                    sub = qs.get("path",["."])[0]
                    res = vault.list(sub)
                    tracer.emit("vault_list", {"path":sub,"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/vault/read_text":
                    p = qs.get("path",[""])[0]
                    res = vault.read_text(p)
                    tracer.emit("vault_read_text", {"path":p,"sha256":res["sha256"],"truncated":res["truncated"],"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/vault/read_bytes":
                    p = qs.get("path",[""])[0]
                    res = vault.read_bytes_b64(p)
                    tracer.emit("vault_read_bytes", {"path":p,"sha256":res["sha256"],"truncated":res["truncated"],"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/vault/info":
                    p = qs.get("path",[""])[0]
                    res = vault.info(p)
                    tracer.emit("vault_info", {"path":p,"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/steer/get":
                    cur = steering.load_profile()
                    tracer.emit("steer_get", {"steering_hash":_profile_hash(cur)})
                    return self._send(200, {"ok":True,"steering":cur,"steering_hash":_profile_hash(cur)})
                if u.path == "/steer/drift":
                    drift = steering.load_drift()
                    tracer.emit("steer_drift", {"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"drift":drift,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/fsd/query":
                    q = qs.get("q",[""])[0]
                    results = fsd_search(q) if q else []
                    if isinstance(results, dict) and "error" in results:
                        tracer.emit("fsd_query_error", {"q":q,"error":results["error"]})
                        return self._send(500, {"ok":False,"error":results["error"]})
                    tracer.emit("fsd_query", {"q":q,"count":len(results),"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"results":results,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/fsd/entry":
                    title = qs.get("title",[""])[0]
                    if not title: return self._err(400, "missing_title")
                    data = fsd_entry(title)
                    if isinstance(data, dict) and "error" in data:
                        tracer.emit("fsd_entry_error", {"title":title,"error":data["error"]})
                        return self._send(500, {"ok":False,"error":data["error"]})
                    tracer.emit("fsd_entry", {"title":title,"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":data,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/fsd/cache_info":
                    idx_path = os.path.join(vault.root_dir, "memory", "ingest", "index.json")
                    try:
                        with open(idx_path, "r", encoding="utf-8") as f: idx = json.load(f)
                        tracer.emit("fsd_cache_info", {"files":len(idx.get("files",[])),"steering_hash":sp_hash})
                        return self._send(200, {"ok":True,"index":idx,"steering":sp,"steering_hash":sp_hash})
                    except Exception as e:
                        return self._err(500, "cache_info_error", {"message":str(e)}, steering_profile=sp)
                return self._err(404, "not_found", steering_profile=sp)
            except PermissionError as e:
                return self._err(403, "permission_denied", {"message":str(e)}, steering_profile=steering.load_profile())
            except FileNotFoundError as e:
                return self._err(404, "not_found", {"message":str(e)}, steering_profile=steering.load_profile())
            except Exception as e:
                return self._err(500, "internal_error", {"message":str(e)}, steering_profile=steering.load_profile())

        def do_POST(self):
            try:
                u      = urlparse(self.path)
                length = int(self.headers.get("Content-Length","0"))
                raw    = self.rfile.read(length) if length > 0 else b"{}"
                try:    data = json.loads(raw.decode("utf-8"))
                except: data = {}
                sp      = preflight_router(u.path, "POST", dict(self.headers), data, steering)
                sp_hash = _profile_hash(sp)

                # ── 原有 vault endpoint ──────────────────────────
                if u.path == "/vault/write_text":
                    p   = data.get("path","")
                    text = data.get("text","")
                    overwrite = bool(data.get("overwrite", True))
                    res = vault.write_text(p, text, overwrite=overwrite)
                    tracer.emit("vault_write_text", {"path":p,"sha256":res["sha256"],"size":res["size"],"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})
                if u.path == "/vault/mkdir":
                    p   = data.get("path","")
                    res = vault.mkdir(p)
                    tracer.emit("vault_mkdir", {"path":p,"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"data":res,"steering":sp,"steering_hash":sp_hash})

                # ── 原有 steering endpoint ───────────────────────
                if u.path == "/steer/set":
                    newp = data.get("profile",{})
                    if not isinstance(newp, dict): return self._err(400, "invalid_profile", steering_profile=sp)
                    rec = steering.save_profile(newp, source="http")
                    tracer.emit("steer_set", {"profile":rec["profile"],"profile_hash":rec["profile_hash"],"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"saved":rec,"steering":rec["profile"],"steering_hash":rec["profile_hash"]})
                if u.path == "/steer/reset":
                    rec = steering.save_profile(DEFAULT_STEERING_PROFILE, source="reset")
                    tracer.emit("steer_reset", {"profile_hash":rec["profile_hash"],"steering_hash":sp_hash})
                    return self._send(200, {"ok":True,"saved":rec,"steering":rec["profile"],"steering_hash":rec["profile_hash"]})

                # ════════════════════════════════════════════════
                # v0.2 補接：Product Gateway（4 個 endpoint）
                # ════════════════════════════════════════════════

                # 1. POST /task/submit ─────────────────────────
                if u.path == "/task/submit":
                    prompt   = data.get("prompt","")
                    category = data.get("category","product")
                    user_id  = data.get("user_id","guest")
                    source   = data.get("source","web")
                    if not prompt:
                        return self._err(400, "prompt_required", steering_profile=sp)
                    result = _pg_submit_task(vault, tracer, prompt, category, user_id, source)
                    return self._send(200, {
                        "ok":True, "task_id":result["task_id"],
                        "status":"accepted", "partial_result":result["partial_result"],
                    })

                # 2. POST /result/partial ──────────────────────
                if u.path == "/result/partial":
                    task_id = data.get("task_id","")
                    if not task_id: return self._err(400, "task_id_required", steering_profile=sp)
                    try:
                        raw_txt = vault.read_text(f"{_P_PARTIAL}/{task_id}.json")["text"]
                        partial = json.loads(raw_txt)
                        return self._send(200, {"ok":True,"task_id":task_id,"partial_result":partial})
                    except FileNotFoundError:
                        return self._err(404, "not_found", steering_profile=sp)

                # 3. POST /billing/confirm ─────────────────────
                if u.path == "/billing/confirm":
                    task_id    = data.get("task_id","")
                    payment_id = data.get("payment_id","")
                    amount     = int(data.get("amount", 299))
                    currency   = data.get("currency","TWD")
                    status     = data.get("status","paid")
                    if not task_id: return self._err(400, "task_id_required", steering_profile=sp)
                    try:
                        vault.read_text(f"{_P_TASKS}/{task_id}.json")
                    except FileNotFoundError:
                        return self._err(404, "task_not_found", steering_profile=sp)
                    ledger = _pg_write_ledger(vault, tracer, task_id, payment_id, amount, currency, status)
                    return self._send(200, {
                        "ok":True, "task_id":task_id,
                        "ledger_status":ledger["status"], "unlock":True,
                    })

                # 4. POST /result/full ─────────────────────────
                if u.path == "/result/full":
                    task_id = data.get("task_id","")
                    if not task_id: return self._err(400, "task_id_required", steering_profile=sp)
                    if not _pg_is_unlocked(vault, task_id):
                        return self._send(402, {"ok":False,"error":"payment_required"})
                    try:
                        full = json.loads(vault.read_text(f"{_P_FULL}/{task_id}.json")["text"])
                        tracer.emit("result_full_view", {"task_id":task_id,"steering_hash":sp_hash})
                        return self._send(200, {"ok":True,"task_id":task_id,"full_result":full})
                    except FileNotFoundError:
                        return self._err(404, "not_found", steering_profile=sp)

                # ════════════════════════════════════════════════

                return self._err(404, "not_found", steering_profile=sp)
            except PermissionError as e:
                return self._err(403, "permission_denied", {"message":str(e)}, steering_profile=steering.load_profile())
            except FileExistsError as e:
                return self._err(409, "already_exists", {"message":str(e)}, steering_profile=steering.load_profile())
            except Exception as e:
                return self._err(500, "internal_error", {"message":str(e)}, steering_profile=steering.load_profile())

        def log_message(self, format, *args):
            return

    return Handler

# -------------------------
# CLI
# -------------------------

def cmd_cli(vault, tracer, steering):
    print("FlowCoreLoop AI Computer CLI v0.2")
    print("Commands: ls, cat, write, mkdir, info, trace_tail, steer_show, steer_set, steer_preset, drift_show, help, exit")
    while True:
        try:
            cmdline = input("ai> ").strip()
        except EOFError:
            cmdline = "exit"
        if not cmdline: continue
        if cmdline == "exit":
            tracer.emit("cli_exit", {})
            break
        parts = cmdline.split(" ", 1)
        cmd   = parts[0]
        arg   = parts[1].strip() if len(parts) > 1 else ""
        try:
            if cmd == "ls":
                res = vault.list(arg or ".")
                tracer.emit("cli_ls", {"path":arg or "."})
                for it in res["items"]:
                    print(f"{'d' if it['type']=='dir' else '-'} {it['size']:>10}  {it['name']}")
                if res["truncated"]: print("... truncated")
            elif cmd == "cat":
                if not arg: print("path required"); continue
                res = vault.read_text(arg)
                tracer.emit("cli_cat", {"path":arg,"sha256":res["sha256"],"truncated":res["truncated"]})
                print(res["text"])
                if res["truncated"]: print("\n... truncated")
            elif cmd == "write":
                if not arg: print("path required"); continue
                print("Enter text. Finish with .end")
                lines = []
                while True:
                    line = input()
                    if line == ".end": break
                    lines.append(line)
                text = "\n".join(lines) + ("\n" if lines else "")
                res = vault.write_text(arg, text, overwrite=True)
                tracer.emit("cli_write", {"path":arg,"sha256":res["sha256"],"size":res["size"]})
                print(f"ok wrote {res['size']} bytes")
            elif cmd == "mkdir":
                if not arg: print("path required"); continue
                vault.mkdir(arg)
                tracer.emit("cli_mkdir", {"path":arg})
                print("ok")
            elif cmd == "info":
                if not arg: print("path required"); continue
                res = vault.info(arg)
                tracer.emit("cli_info", {"path":arg})
                print(_json_dumps(res))
            elif cmd == "trace_tail":
                n = int(arg) if arg else 5
                path = os.path.join(tracer.log_dir, "trace.jsonl")
                if not os.path.exists(path): print("no trace yet"); continue
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.readlines()[-n:]
                for ln in lines: print(ln.rstrip("\n"))
            elif cmd == "steer_show":
                prof = steering.load_profile()
                tracer.emit("cli_steer_show", {"steering":prof,"steering_hash":_profile_hash(prof)})
                print(_json_dumps({"steering":prof,"steering_hash":_profile_hash(prof)}))
            elif cmd == "drift_show":
                d = steering.load_drift()
                tracer.emit("cli_drift_show", {"steering_hash":_profile_hash(steering.load_profile())})
                print(_json_dumps(d))
            elif cmd == "steer_set":
                toks = arg.split()
                if len(toks) != 2: print("usage: steer_set <key> <value>"); continue
                k, v = toks[0], toks[1]
                if k not in ("explain_depth","inference_scope","deliver_priority","guard_sensitivity"):
                    print("invalid key"); continue
                cur = steering.load_profile()
                cur[k] = _clamp01(v)
                rec = steering.save_profile(cur, source="cli")
                tracer.emit("cli_steer_set", {"key":k,"value":cur[k],"profile_hash":rec["profile_hash"]})
                print(_json_dumps({"ok":True,"saved":rec}))
            elif cmd == "steer_preset":
                name = (arg or "").strip().lower()
                if name not in ("direct","deliver","engineer","risk"):
                    print("usage: steer_preset direct|deliver|engineer|risk"); continue
                prof = steering.load_profile()
                if name == "direct":   prof.update({"explain_depth":0.05,"inference_scope":0.05,"deliver_priority":0.95})
                elif name == "deliver":prof.update({"explain_depth":0.10,"inference_scope":0.05,"deliver_priority":1.00})
                elif name == "engineer":prof.update({"explain_depth":0.20,"inference_scope":0.05,"deliver_priority":0.85,"guard_sensitivity":0.25})
                elif name == "risk":   prof.update({"guard_sensitivity":0.85,"explain_depth":max(prof.get("explain_depth",0.15),0.35)})
                rec = steering.save_profile(prof, source=f"preset:{name}")
                tracer.emit("cli_steer_preset", {"name":name,"profile_hash":rec["profile_hash"]})
                print(_json_dumps({"ok":True,"saved":rec}))
            else:
                print("unknown command")
        except Exception as e:
            tracer.emit("cli_error", {"cmd":cmdline,"error":str(e)})
            print(f"error: {e}")

def cmd_serve(vault, tracer, steering, host, port):
    Handler = make_handler(vault, tracer, steering)
    httpd   = ThreadingHTTPServer((host, port), Handler)
    tracer.emit("server_start", {"host":host,"port":port,"vault_root":vault.root_dir,"steering_hash":_profile_hash(steering.load_profile())})
    print(f"FlowCoreLoop v{VERSION} HTTP → http://{host}:{port}")
    print("Endpoints: /health /vault/* /steer/* /fsd/* /task/submit /result/partial /billing/confirm /result/full")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        tracer.emit("server_stop", {})
        httpd.server_close()

def build_argparser():
    shared = argparse.ArgumentParser(add_help=False)
    shared.add_argument("--vault-root", default=os.environ.get("FLOW_VAULT_ROOT","."))
    shared.add_argument("--persona-id", default=os.environ.get("FLOW_PERSONA_ID","PartnerPersona"))
    shared.add_argument("--rid",        default=os.environ.get("FLOW_RID", None))
    p   = argparse.ArgumentParser(prog="flowcore_loop.py")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("cli",   parents=[shared])
    s = sub.add_parser("serve", parents=[shared])
    s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=int(os.environ.get("FLOW_PORT","8787")))
    i = sub.add_parser("index", parents=[shared])
    i.add_argument("--out",       default="artifact_index.json")
    i.add_argument("--max-files", type=int, default=5000)
    fsd_s = sub.add_parser("fsd_search", parents=[shared])
    fsd_s.add_argument("query");  fsd_s.add_argument("--limit", type=int, default=20)
    fsd_e = sub.add_parser("fsd_entry",  parents=[shared])
    fsd_e.add_argument("title")
    return p

def cmd_index(vault, tracer, out_path, max_files):
    root    = pathlib.Path(vault.root_dir)
    entries = []
    count   = 0
    for p in root.rglob("*"):
        if count >= max_files: break
        try:
            if p.is_file():
                rel = str(p.relative_to(root))
                st  = p.stat()
                h   = hashlib.sha256()
                with open(p, "rb") as f: chunk = f.read(2_000_000)
                h.update(chunk)
                entries.append({"path":rel,"size":st.st_size,"mtime":int(st.st_mtime),"sha256_head_2mb":h.hexdigest()})
                count += 1
        except Exception:
            continue
    out_full = os.path.join(vault.root_dir, out_path)
    with open(out_full, "w", encoding="utf-8") as f:
        json.dump({"origin_signature":ORIGIN_SIGNATURE,"module_name":"ArtifactIndex","created_at":now_iso(),"vault_root":vault.root_dir,"max_files":max_files,"files":entries}, f, ensure_ascii=False, indent=2)
    tracer.emit("index_built", {"out":out_path,"files":len(entries)})
    print(f"ok: wrote {out_full} with {len(entries)} files")

def main():
    ap   = build_argparser()
    args = ap.parse_args()
    vault    = Vault(args.vault_root)
    log_dir  = os.path.join(os.path.dirname(__file__), "log")
    tracer   = Tracer(log_dir=log_dir, persona_id=args.persona_id, rid=args.rid)
    steering = SteeringStore(dir_path=log_dir)
    _        = steering.save_profile(steering.load_profile(), source="boot")
    tracer.emit("boot", {"version":VERSION,"vault_root":vault.root_dir,"steering_hash":_profile_hash(steering.load_profile())})
    if args.cmd == "cli":       return cmd_cli(vault, tracer, steering)
    if args.cmd == "serve":     return cmd_serve(vault, tracer, steering, args.host, args.port)
    if args.cmd == "index":     return cmd_index(vault, tracer, args.out, args.max_files)
    if args.cmd == "fsd_search":
        res = fsd_search(args.query, args.limit)
        tracer.emit("cli_fsd_search", {"q":args.query,"count":len(res) if isinstance(res,list) else -1})
        print(_json_dumps(res)); return
    if args.cmd == "fsd_entry":
        res = fsd_entry(args.title)
        tracer.emit("cli_fsd_entry", {"title":args.title})
        print(res if not isinstance(res,dict) else _json_dumps(res)); return
    raise SystemExit(2)

if __name__ == "__main__":
    main()
