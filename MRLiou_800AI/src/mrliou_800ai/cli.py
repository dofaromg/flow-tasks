from __future__ import annotations
import argparse, json
from pathlib import Path
from .config import ROOT
from .trace import TraceChain
from .datastore import ReversibleStore
from .registry import AgentRegistry
from .audit import EngineeringGate
from .orchestrator import Orchestrator
from .api import APIServer
from .physics.pipeline import audit_npz

def runtime():
    trace = TraceChain(ROOT / "logs")
    registry = AgentRegistry(ROOT / "config")
    store = ReversibleStore(ROOT, trace)
    orchestrator = Orchestrator(registry, EngineeringGate(), trace)
    return trace, registry, store, orchestrator

def main(argv=None):
    p = argparse.ArgumentParser(prog="mrliou-800ai")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1"); s.add_argument("--port", type=int, default=8787)
    sub.add_parser("health"); sub.add_parser("agents")
    d = sub.add_parser("dispatch"); d.add_argument("--task", required=True)
    m = sub.add_parser("mass-audit"); m.add_argument("--data", required=True); m.add_argument("--out", required=True)
    args = p.parse_args(argv)
    trace, registry, store, orchestrator = runtime()
    if args.cmd == "serve": APIServer(args.host, args.port, registry, orchestrator, store, trace).serve()
    elif args.cmd == "health": print(json.dumps({"ok": True, "root": str(ROOT), "origin_signature":"MrLiouWord"}, indent=2))
    elif args.cmd == "agents": print(json.dumps(registry.list_agents(), indent=2, ensure_ascii=False))
    elif args.cmd == "dispatch": print(json.dumps(orchestrator.dispatch(args.task), indent=2, ensure_ascii=False))
    elif args.cmd == "mass-audit": print(json.dumps(audit_npz(args.data, args.out), indent=2))

if __name__ == "__main__": main()
