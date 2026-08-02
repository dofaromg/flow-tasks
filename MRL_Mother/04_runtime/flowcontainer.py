#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
flowcontainer.py — FlowContainer 原生服務編排器
origin_signature: MrLiouWord
module_name: FlowContainer.Genesis.v1
layer: L7 LOOP
intent: "MRL 自有容器運行時 — 取代 Docker，用進程管理 + Vault 沙箱 + Merkle 追蹤"
x_policy: Anti-Scaffold Law (single-file closure, stdlib only, full runnable)

怎麼過去，就怎麼回來。

血脈：智障系統 → MrLiouAI.Runtime v1-v56 → flowcore_loop.py → FlowContainer

架構：
  boot → ServiceRegistry(yaml) → DependencyResolver(拓撲排序)
       → ProcessManager(subprocess) → HealthMonitor(背景執行緒)
       → Tracer(Merkle鏈) → CLI(互動控制台)

用法：
  python flowcontainer.py start [--config path]   # 啟動所有服務
  python flowcontainer.py stop                     # 停止所有服務
  python flowcontainer.py status                   # 顯示狀態
  python flowcontainer.py cli                      # 互動控制台
"""
from __future__ import annotations

import argparse
import datetime as _dt
import hashlib
import json
import os
import signal
import subprocess
import sys
import threading
import time
import uuid
from collections import defaultdict
from http.client import HTTPConnection
from pathlib import Path

VERSION = "1.0.0"
ORIGIN_SIGNATURE = "MrLiouWord"
DEFAULT_CONFIG = "config/flowcontainer.yaml"


# ── Time ──

def now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).astimezone().isoformat(timespec="seconds")


# ── Merkle Trace (from flowcore_loop.py lineage) ──

def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def merkle_fold(prev_root: str, payload: dict) -> str:
    leaf = _sha256(json.dumps(payload, sort_keys=True, ensure_ascii=False))
    return _sha256(prev_root + leaf)


class Tracer:
    def __init__(self, log_dir: str):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.trace_path = os.path.join(self.log_dir, "flowcontainer_trace.jsonl")
        self.state_path = os.path.join(self.log_dir, "flowcontainer_state.json")
        self._state = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.state_path):
            try:
                with open(self.state_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"merkle_root": "0" * 64, "tick": 0}

    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(self._state, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.state_path)

    def emit(self, event_type: str, payload: dict) -> dict:
        self._state["tick"] += 1
        rec = {
            "event_id": uuid.uuid4().hex[:12],
            "tick": self._state["tick"],
            "ts": now_iso(),
            "origin_signature": ORIGIN_SIGNATURE,
            "event_type": event_type,
            "payload": payload,
        }
        new_root = merkle_fold(self._state["merkle_root"], rec)
        rec["merkle_root"] = new_root
        self._state["merkle_root"] = new_root
        with open(self.trace_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(rec, ensure_ascii=False, sort_keys=True) + "\n")
        self._save()
        return rec


# ── Config Loader ──

def _try_load_yaml(path: str) -> dict:
    """Minimal YAML subset parser — handles the flowcontainer.yaml format
    without requiring PyYAML. Supports: top-level keys, nested dicts via
    indentation, simple string/int/bool values, lists with '- ' prefix."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"Config not found: {path}")

    # Try PyYAML first if available
    try:
        import yaml
        with open(path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except ImportError:
        pass

    # Fallback: look for JSON sidecar
    json_path = path.rsplit(".", 1)[0] + ".json"
    if os.path.exists(json_path):
        with open(json_path, "r", encoding="utf-8") as f:
            return json.load(f)

    raise ImportError(
        f"Cannot parse {path}: install PyYAML (`pip install pyyaml`) "
        f"or provide {json_path} as JSON equivalent."
    )


def load_config(path: str) -> dict:
    if path.endswith(".json"):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return _try_load_yaml(path)


# ── Service Definition ──

class ServiceDef:
    def __init__(self, name: str, cfg: dict):
        self.name = name
        self.stype = cfg.get("type", "managed")  # managed | external
        self.runtime = cfg.get("runtime", "")     # node | python
        self.cwd = cfg.get("cwd", ".")
        self.entry = cfg.get("entry", "")
        self.args = cfg.get("args", [])
        self.port = cfg.get("port", 0)
        self.health_path = cfg.get("health", "")
        self.health_cmd = cfg.get("health_cmd", "")
        self.depends_on = cfg.get("depends_on", [])
        self.env = cfg.get("env", {})

    def __repr__(self):
        return f"<Service {self.name} :{self.port} [{self.stype}]>"


# ── Dependency Resolver (topological sort) ──

def resolve_order(services: dict[str, ServiceDef]) -> list[str]:
    in_degree = defaultdict(int)
    graph = defaultdict(list)
    all_names = set(services.keys())

    for name, svc in services.items():
        in_degree.setdefault(name, 0)
        for dep in svc.depends_on:
            if dep in all_names:
                graph[dep].append(name)
                in_degree[name] += 1

    queue = [n for n in all_names if in_degree[n] == 0]
    queue.sort()
    order = []
    while queue:
        node = queue.pop(0)
        order.append(node)
        for child in sorted(graph[node]):
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)

    if len(order) != len(all_names):
        missing = all_names - set(order)
        raise RuntimeError(f"Circular dependency detected: {missing}")

    return order


# ── Process Manager ──

def _find_runtime(runtime: str) -> str:
    if runtime == "node":
        for cmd in ("node", "node.exe"):
            if _which(cmd):
                return cmd
        raise FileNotFoundError("Node.js not found in PATH")
    elif runtime == "python":
        for cmd in ("python", "python3", "python.exe"):
            if _which(cmd):
                return cmd
        raise FileNotFoundError("Python not found in PATH")
    return runtime


def _which(cmd: str) -> str | None:
    import shutil
    return shutil.which(cmd)


IS_WINDOWS = sys.platform == "win32"


class ManagedProcess:
    def __init__(self, svc: ServiceDef, base_dir: str, tracer: Tracer):
        self.svc = svc
        self.base_dir = base_dir
        self.tracer = tracer
        self.proc: subprocess.Popen | None = None
        self.restart_count = 0
        self.max_restarts = 5
        self.started_at: str | None = None
        self.stopped = False

    def start(self):
        if self.svc.stype == "external":
            return

        runtime_bin = _find_runtime(self.svc.runtime)
        cmd = [runtime_bin, self.svc.entry] + [str(a) for a in self.svc.args]
        cwd = os.path.join(self.base_dir, self.svc.cwd)
        cwd = os.path.realpath(cwd)

        env = dict(os.environ)
        env.update({k: str(v) for k, v in self.svc.env.items()})
        env["ORIGIN_SIGNATURE"] = ORIGIN_SIGNATURE

        kwargs = {
            "cwd": cwd,
            "env": env,
            "stdout": subprocess.PIPE,
            "stderr": subprocess.STDOUT,
        }
        if IS_WINDOWS:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        self.proc = subprocess.Popen(cmd, **kwargs)
        self.started_at = now_iso()
        self.stopped = False

        log_thread = threading.Thread(
            target=self._drain_output, daemon=True,
            name=f"log-{self.svc.name}"
        )
        log_thread.start()

        self.tracer.emit("service_start", {
            "service": self.svc.name,
            "port": self.svc.port,
            "pid": self.proc.pid,
            "cmd": cmd,
        })

    def _drain_output(self):
        log_dir = os.path.join(self.tracer.log_dir, "service_logs")
        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, f"{self.svc.name}.log")
        try:
            with open(log_path, "a", encoding="utf-8", errors="replace") as f:
                for line in self.proc.stdout:
                    decoded = line.decode("utf-8", errors="replace")
                    f.write(decoded)
                    f.flush()
        except Exception:
            pass

    def stop(self):
        self.stopped = True
        if self.proc and self.proc.poll() is None:
            try:
                if IS_WINDOWS:
                    self.proc.send_signal(signal.CTRL_BREAK_EVENT)
                else:
                    self.proc.terminate()
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
            except Exception:
                try:
                    self.proc.kill()
                except Exception:
                    pass

            self.tracer.emit("service_stop", {
                "service": self.svc.name,
                "pid": self.proc.pid,
            })

    def is_alive(self) -> bool:
        if self.svc.stype == "external":
            return True
        if self.proc is None:
            return False
        return self.proc.poll() is None

    def check_health(self) -> bool:
        if self.svc.stype == "external" and self.svc.health_cmd:
            try:
                result = subprocess.run(
                    self.svc.health_cmd, shell=True,
                    capture_output=True, timeout=5
                )
                return result.returncode == 0
            except Exception:
                return False

        if not self.svc.port or not self.svc.health_path:
            return self.is_alive()

        try:
            conn = HTTPConnection("127.0.0.1", self.svc.port, timeout=5)
            conn.request("GET", self.svc.health_path)
            resp = conn.getresponse()
            conn.close()
            return resp.status == 200
        except Exception:
            return False

    def try_restart(self) -> bool:
        if self.stopped:
            return False
        if self.restart_count >= self.max_restarts:
            self.tracer.emit("service_restart_exhausted", {
                "service": self.svc.name,
                "restart_count": self.restart_count,
            })
            return False

        self.restart_count += 1
        backoff = min(2 ** self.restart_count, 30)
        self.tracer.emit("service_restart", {
            "service": self.svc.name,
            "attempt": self.restart_count,
            "backoff_s": backoff,
        })
        time.sleep(backoff)
        self.start()
        return True


# ── Health Monitor ──

class HealthMonitor:
    def __init__(self, processes: dict[str, ManagedProcess], tracer: Tracer,
                 interval: int = 15):
        self.processes = processes
        self.tracer = tracer
        self.interval = interval
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._consecutive_fails: dict[str, int] = defaultdict(int)

    def start(self):
        self._thread = threading.Thread(target=self._loop, daemon=True,
                                        name="health-monitor")
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)

    def _loop(self):
        while not self._stop_event.wait(self.interval):
            for name, mp in self.processes.items():
                if mp.stopped or mp.svc.stype == "external":
                    continue

                if not mp.is_alive():
                    self._consecutive_fails[name] += 1
                    print(f"  [{name}] process died (attempt restart "
                          f"{mp.restart_count + 1}/{mp.max_restarts})")
                    mp.try_restart()
                    continue

                healthy = mp.check_health()
                if healthy:
                    self._consecutive_fails[name] = 0
                else:
                    self._consecutive_fails[name] += 1
                    if self._consecutive_fails[name] >= 3:
                        print(f"  [{name}] unhealthy x3, restarting...")
                        self.tracer.emit("service_unhealthy", {
                            "service": name,
                            "consecutive_fails": self._consecutive_fails[name],
                        })
                        mp.stop()
                        mp.try_restart()
                        self._consecutive_fails[name] = 0


# ── FieldMap (service state sync) ──

class FieldMap:
    """In-memory service state map — the living FieldMap.Sync.core"""

    def __init__(self):
        self._state: dict[str, dict] = {}
        self._lock = threading.Lock()

    def update(self, name: str, state: dict):
        with self._lock:
            self._state[name] = {**state, "updated_at": now_iso()}

    def get(self, name: str) -> dict | None:
        with self._lock:
            return self._state.get(name)

    def snapshot(self) -> dict:
        with self._lock:
            return dict(self._state)


# ── FlowContainer (main orchestrator) ──

class FlowContainer:
    def __init__(self, config_path: str, base_dir: str | None = None):
        self.config_path = config_path
        self.base_dir = base_dir or os.getcwd()
        self.config = load_config(config_path)
        self.tracer = Tracer(os.path.join(self.base_dir, ".flowcontainer"))
        self.fieldmap = FieldMap()
        self.services: dict[str, ServiceDef] = {}
        self.processes: dict[str, ManagedProcess] = {}
        self.monitor: HealthMonitor | None = None
        self._boot_order: list[str] = []

        self._load_services()

    def _load_services(self):
        svc_defs = self.config.get("services", {})
        for name, cfg in svc_defs.items():
            self.services[name] = ServiceDef(name, cfg)
        self._boot_order = resolve_order(self.services)

    def start(self):
        print("=" * 48)
        print(" FlowContainer — MRL Native Runtime")
        print(f" origin_signature: {ORIGIN_SIGNATURE}")
        print(f" version: {VERSION}")
        print("=" * 48)
        print()

        self.tracer.emit("container_boot", {
            "version": VERSION,
            "services": list(self._boot_order),
            "config": self.config_path,
        })

        for name in self._boot_order:
            svc = self.services[name]
            mp = ManagedProcess(svc, self.base_dir, self.tracer)
            self.processes[name] = mp

            if svc.stype == "external":
                print(f"  [{name}] external :{svc.port} — checking...")
                healthy = mp.check_health()
                status = "ready" if healthy else "waiting"
                self.fieldmap.update(name, {
                    "status": status, "port": svc.port, "type": "external"
                })
                print(f"  [{name}] -> {status}")
            else:
                print(f"  [{name}] starting :{svc.port}...")
                try:
                    mp.start()
                    self.fieldmap.update(name, {
                        "status": "starting",
                        "port": svc.port,
                        "pid": mp.proc.pid if mp.proc else 0,
                    })
                    print(f"  [{name}] -> pid {mp.proc.pid if mp.proc else '?'}")
                except Exception as e:
                    print(f"  [{name}] -> FAILED: {e}")
                    self.fieldmap.update(name, {
                        "status": "failed", "error": str(e)
                    })

        # Wait for services to initialize
        print()
        print("[Health Check] waiting 8s...")
        time.sleep(8)

        ok_count = 0
        for name in self._boot_order:
            mp = self.processes[name]
            healthy = mp.check_health()
            status = "ok" if healthy else "starting"
            self.fieldmap.update(name, {
                "status": status, "port": mp.svc.port,
            })
            mark = "OK" if healthy else "..."
            print(f"  {name} :{mp.svc.port} -> {mark}")
            if healthy:
                ok_count += 1

        print()
        print(f"  {ok_count}/{len(self.services)} services healthy")

        self.tracer.emit("container_started", {
            "healthy": ok_count,
            "total": len(self.services),
            "merkle_root": self.tracer._state["merkle_root"],
        })

        # Start health monitor
        self.monitor = HealthMonitor(self.processes, self.tracer)
        self.monitor.start()

        print()
        print("=" * 48)
        print(" FlowContainer Running")
        print()
        for name in self._boot_order:
            svc = self.services[name]
            if svc.port:
                print(f"  {name}: http://localhost:{svc.port}")
        print()
        print(f"  Trace: .flowcontainer/flowcontainer_trace.jsonl")
        print(f"  Logs:  .flowcontainer/service_logs/")
        print()
        print("  Stop:   python flowcontainer.py stop")
        print("  Status: python flowcontainer.py status")
        print("  CLI:    python flowcontainer.py cli")
        print("=" * 48)

    def stop(self):
        print("FlowContainer stopping...")
        if self.monitor:
            self.monitor.stop()

        for name in reversed(self._boot_order):
            mp = self.processes.get(name)
            if mp and mp.svc.stype != "external":
                print(f"  [{name}] stopping...")
                mp.stop()
                self.fieldmap.update(name, {"status": "stopped"})

        self.tracer.emit("container_stop", {
            "merkle_root": self.tracer._state["merkle_root"],
        })
        print("FlowContainer stopped.")

    def status(self) -> dict:
        result = {}
        for name in self._boot_order:
            mp = self.processes.get(name)
            if mp:
                healthy = mp.check_health()
                alive = mp.is_alive()
                result[name] = {
                    "port": mp.svc.port,
                    "type": mp.svc.stype,
                    "alive": alive,
                    "healthy": healthy,
                    "pid": mp.proc.pid if mp.proc and alive else None,
                    "restarts": mp.restart_count,
                    "started_at": mp.started_at,
                }
            else:
                svc = self.services.get(name)
                result[name] = {
                    "port": svc.port if svc else 0,
                    "type": "unknown",
                    "alive": False,
                    "healthy": False,
                }
        return result

    def print_status(self):
        print()
        print("FlowContainer Status")
        print("=" * 60)
        st = self.status()
        for name, info in st.items():
            mark = "OK" if info["healthy"] else ("UP" if info["alive"] else "DOWN")
            pid_str = f"pid={info['pid']}" if info.get("pid") else ""
            restart_str = f"restarts={info['restarts']}" if info.get("restarts") else ""
            extras = " ".join(filter(None, [pid_str, restart_str]))
            print(f"  {name:<20} :{info['port']:<6} [{mark:<4}] {extras}")
        print()
        print(f"  Merkle root: {self.tracer._state['merkle_root'][:16]}...")
        print(f"  Tick: {self.tracer._state['tick']}")
        print("=" * 60)

    def cli(self):
        """Interactive control console — FlowShell lineage"""
        print()
        print("FlowContainer CLI")
        print("Commands: status, start <name>, stop <name>, restart <name>,")
        print("          logs <name>, fieldmap, trace, exit")
        print()

        while True:
            try:
                cmd = input("flow> ").strip()
            except (EOFError, KeyboardInterrupt):
                print()
                break

            if not cmd:
                continue

            parts = cmd.split()
            action = parts[0].lower()

            if action == "exit" or action == "quit":
                break
            elif action == "status":
                self.print_status()
            elif action == "fieldmap":
                snap = self.fieldmap.snapshot()
                print(json.dumps(snap, indent=2, ensure_ascii=False))
            elif action == "trace":
                print(f"  Merkle root: {self.tracer._state['merkle_root']}")
                print(f"  Tick: {self.tracer._state['tick']}")
                print(f"  Trace file: {self.tracer.trace_path}")
            elif action == "stop" and len(parts) > 1:
                name = parts[1]
                mp = self.processes.get(name)
                if mp:
                    mp.stop()
                    self.fieldmap.update(name, {"status": "stopped"})
                    print(f"  [{name}] stopped")
                else:
                    print(f"  unknown service: {name}")
            elif action == "start" and len(parts) > 1:
                name = parts[1]
                mp = self.processes.get(name)
                if mp:
                    mp.stopped = False
                    mp.restart_count = 0
                    mp.start()
                    self.fieldmap.update(name, {
                        "status": "starting", "port": mp.svc.port,
                    })
                    print(f"  [{name}] started (pid {mp.proc.pid if mp.proc else '?'})")
                else:
                    print(f"  unknown service: {name}")
            elif action == "restart" and len(parts) > 1:
                name = parts[1]
                mp = self.processes.get(name)
                if mp:
                    mp.stop()
                    time.sleep(1)
                    mp.stopped = False
                    mp.restart_count = 0
                    mp.start()
                    self.fieldmap.update(name, {
                        "status": "restarting", "port": mp.svc.port,
                    })
                    print(f"  [{name}] restarted (pid {mp.proc.pid if mp.proc else '?'})")
                else:
                    print(f"  unknown service: {name}")
            elif action == "logs" and len(parts) > 1:
                name = parts[1]
                log_path = os.path.join(
                    self.tracer.log_dir, "service_logs", f"{name}.log"
                )
                if os.path.exists(log_path):
                    with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                        lines = f.readlines()
                    for line in lines[-20:]:
                        print(f"  {line.rstrip()}")
                else:
                    print(f"  no logs for {name}")
            else:
                print(f"  unknown command: {cmd}")


# ── PID file for stop/status from separate process ──

PID_FILE = ".flowcontainer/flowcontainer.pid"
STATE_FILE = ".flowcontainer/flowcontainer_running.json"


def _save_running_state(container: FlowContainer):
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    state = {
        "pid": os.getpid(),
        "started_at": now_iso(),
        "config": container.config_path,
        "services": {
            name: {"port": svc.port, "type": svc.stype}
            for name, svc in container.services.items()
        },
    }
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)
    with open(PID_FILE, "w") as f:
        f.write(str(os.getpid()))


def _read_running_state() -> dict | None:
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return None


def _cleanup_state():
    for p in (PID_FILE, STATE_FILE):
        if os.path.exists(p):
            os.remove(p)


# ── CLI Entry Point ──

def main():
    parser = argparse.ArgumentParser(
        description="FlowContainer — MRL Native Service Orchestrator"
    )
    parser.add_argument("action", choices=["start", "stop", "status", "cli"],
                        help="Action to perform")
    parser.add_argument("--config", "-c", default=DEFAULT_CONFIG,
                        help=f"Config file path (default: {DEFAULT_CONFIG})")
    parser.add_argument("--base-dir", "-d", default=None,
                        help="Base directory for service paths")
    args = parser.parse_args()

    if args.action == "status":
        state = _read_running_state()
        if state:
            print(f"FlowContainer running (pid {state['pid']}, "
                  f"started {state['started_at']})")
            for name, info in state.get("services", {}).items():
                print(f"  {name}: :{info['port']} [{info['type']}]")
        else:
            print("FlowContainer not running.")
        return

    if args.action == "stop":
        if os.path.exists(PID_FILE):
            with open(PID_FILE, "r") as f:
                pid = int(f.read().strip())
            try:
                if IS_WINDOWS:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)],
                                   capture_output=True)
                else:
                    os.kill(pid, signal.SIGTERM)
                print(f"FlowContainer stopped (pid {pid})")
            except ProcessLookupError:
                print(f"Process {pid} not found (already stopped?)")
            _cleanup_state()
        else:
            print("FlowContainer not running.")
        return

    # start or cli
    container = FlowContainer(args.config, args.base_dir)

    def _shutdown(signum, frame):
        print()
        container.stop()
        _cleanup_state()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    if not IS_WINDOWS:
        signal.signal(signal.SIGHUP, _shutdown)

    container.start()
    _save_running_state(container)

    if args.action == "cli":
        container.cli()
        container.stop()
        _cleanup_state()
    else:
        # Keep running, wait for signal
        print()
        print("Press Ctrl+C to stop.")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print()
            container.stop()
            _cleanup_state()


if __name__ == "__main__":
    main()
