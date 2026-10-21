#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
world_module.py — World Module / Particle Globe Entry Point
origin_signature: MrLiouWord
layer: L4 WORLD

This module is the official entry point for the WorldModule core group (Y=4).
It manages:
  - World nodes  (named memory-particle positions in the world graph)
  - World state  (key-value snapshot of the living world)
  - World trajectory  (ordered history of state transitions)
  - Particle globe coordinates  (lat/lon/alt mapping for 3-D visualisation)

Design principle: 怎麼過去，就怎麼回來 (the path forward is the path back)
All state mutations are recorded as reversible trajectory entries so the
entire world can be rewound to any prior snapshot.

Usage (as a library)
---------------------
    from world_module import WorldModule

    world = WorldModule()
    world.set_node("FlowSeed", {"type": "persona", "layer": "L1"})
    world.set_state("active_persona", "FlowSeed")
    snap = world.snapshot()

Usage (CLI)
-----------
    python 05_persona/world_module.py set   --node FlowSeed --data '{"type":"persona"}'
    python 05_persona/world_module.py get   --node FlowSeed
    python 05_persona/world_module.py state --key active_persona --value FlowSeed
    python 05_persona/world_module.py snap
    python 05_persona/world_module.py rewind --step 1
    python 05_persona/world_module.py globe  --node FlowSeed --lat 25.0 --lon 121.5
"""

from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import time
from typing import Any, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"
WORLD_VERSION = "1.0"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WORLD_DIR = _REPO_ROOT / "05_persona" / "_data" / "world"


# ─── Helpers ─────────────────────────────────────────────────────────────────

def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now_ms() -> int:
    return int(time.time() * 1000)


def _load_json(path: pathlib.Path, default: Any = None) -> Any:
    if path.exists():
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    return default if default is not None else {}


def _save_json(path: pathlib.Path, obj: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


# ─── WorldModule ─────────────────────────────────────────────────────────────

class WorldModule:
    """
    Manages the living world: nodes, key-value state, trajectory, and globe
    coordinates. All mutations are recorded as trajectory steps, enabling
    full rewind to any prior snapshot.
    """

    def __init__(self, data_dir: pathlib.Path = _WORLD_DIR) -> None:
        self.data_dir = pathlib.Path(data_dir)
        self._nodes_path = self.data_dir / "nodes.json"
        self._state_path = self.data_dir / "state.json"
        self._traj_path = self.data_dir / "trajectory.jsonl"
        self._globe_path = self.data_dir / "globe.json"

        self._nodes: Dict[str, Any] = _load_json(self._nodes_path, {})
        self._state: Dict[str, Any] = _load_json(self._state_path, {})
        self._globe: Dict[str, Any] = _load_json(self._globe_path, {})

    # ── Nodes ─────────────────────────────────────────────────────────────────

    def set_node(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create or update a world node."""
        entry = {
            "name": name,
            "data": data,
            "updated_at_ms": _now_ms(),
            "hash": _sha256(data),
        }
        self._nodes[name] = entry
        _save_json(self._nodes_path, self._nodes)
        self._record_trajectory("set_node", {"name": name, "hash": entry["hash"]})
        return entry

    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        """Return a node by name, or None."""
        return self._nodes.get(name)

    def list_nodes(self) -> List[str]:
        return sorted(self._nodes.keys())

    # ── State ─────────────────────────────────────────────────────────────────

    def set_state(self, key: str, value: Any) -> None:
        """Set a world-state key."""
        self._state[key] = value
        _save_json(self._state_path, self._state)
        self._record_trajectory("set_state", {"key": key})

    def get_state(self, key: str, default: Any = None) -> Any:
        return self._state.get(key, default)

    def snapshot(self) -> Dict[str, Any]:
        """Return an immutable snapshot of the current world state."""
        snap = {
            "world_version": WORLD_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "snapshot_at_ms": _now_ms(),
            "nodes": dict(self._nodes),
            "state": dict(self._state),
            "globe": dict(self._globe),
        }
        snap["hash"] = _sha256(snap)
        return snap

    # ── Globe coordinates ─────────────────────────────────────────────────────

    def set_globe_coord(
        self,
        node_name: str,
        lat: float,
        lon: float,
        alt: float = 0.0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Attach a geographic / particle-globe coordinate to a node."""
        coord = {
            "lat": lat,
            "lon": lon,
            "alt": alt,
            "meta": meta or {},
            "updated_at_ms": _now_ms(),
        }
        self._globe[node_name] = coord
        _save_json(self._globe_path, self._globe)
        self._record_trajectory("set_globe_coord", {"node": node_name, "lat": lat, "lon": lon})
        return coord

    def get_globe_coord(self, node_name: str) -> Optional[Dict[str, Any]]:
        return self._globe.get(node_name)

    # ── Trajectory ───────────────────────────────────────────────────────────

    def _record_trajectory(self, action: str, detail: Dict[str, Any]) -> None:
        step = {
            "ts_ms": _now_ms(),
            "action": action,
            "detail": detail,
            "state_hash": _sha256(self._state),
        }
        self._traj_path.parent.mkdir(parents=True, exist_ok=True)
        with self._traj_path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(step, ensure_ascii=False) + "\n")

    def trajectory(self) -> List[Dict[str, Any]]:
        """Return the full ordered list of trajectory steps."""
        if not self._traj_path.exists():
            return []
        steps: List[Dict[str, Any]] = []
        with self._traj_path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    steps.append(json.loads(line))
        return steps

    def rewind(self, steps: int = 1) -> Tuple[bool, str]:
        """
        Remove the last *steps* trajectory entries and reload state from the
        most recent saved files.

        Note: rewind undoes trajectory records but does NOT mutate node/state
        files automatically — it signals that the caller should restore from
        a prior snapshot. To do a full state rewind, restore nodes.json and
        state.json from a snapshot before calling rewind().
        """
        traj = self.trajectory()
        if steps >= len(traj):
            # Clear entire trajectory
            self._traj_path.write_text("", encoding="utf-8")
            return True, "trajectory cleared"
        kept = traj[:-steps]
        self._traj_path.parent.mkdir(parents=True, exist_ok=True)
        with self._traj_path.open("w", encoding="utf-8") as f:
            for step in kept:
                f.write(json.dumps(step, ensure_ascii=False) + "\n")
        return True, f"rewound {steps} step(s)"


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_set_node(args: argparse.Namespace) -> None:
    world = WorldModule()
    data = json.loads(args.data)
    entry = world.set_node(args.node, data)
    print(f"✅ Node set: {args.node}  (hash={entry['hash'][:12]}…)")


def _cmd_get_node(args: argparse.Namespace) -> None:
    world = WorldModule()
    node = world.get_node(args.node)
    if node is None:
        print(f"Node not found: {args.node}")
    else:
        print(json.dumps(node, ensure_ascii=False, indent=2))


def _cmd_state(args: argparse.Namespace) -> None:
    world = WorldModule()
    if args.value is not None:
        world.set_state(args.key, args.value)
        print(f"✅ State set: {args.key} = {args.value}")
    else:
        val = world.get_state(args.key)
        print(json.dumps({args.key: val}, ensure_ascii=False, indent=2))


def _cmd_snap(args: argparse.Namespace) -> None:  # noqa: ARG001
    world = WorldModule()
    snap = world.snapshot()
    print(json.dumps(snap, ensure_ascii=False, indent=2))


def _cmd_rewind(args: argparse.Namespace) -> None:
    world = WorldModule()
    ok, msg = world.rewind(args.step)
    print(f"{'✅' if ok else '❌'} {msg}")


def _cmd_globe(args: argparse.Namespace) -> None:
    world = WorldModule()
    coord = world.set_globe_coord(args.node, args.lat, args.lon)
    print(f"✅ Globe coord set for '{args.node}': lat={coord['lat']}, lon={coord['lon']}")


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="WorldModule — particle globe & world state entry")
    sub = p.add_subparsers(dest="cmd", required=True)

    sn = sub.add_parser("set", help="Create or update a world node")
    sn.add_argument("--node", required=True)
    sn.add_argument("--data", required=True, help="JSON string for node data")

    gn = sub.add_parser("get", help="Get a world node")
    gn.add_argument("--node", required=True)

    st = sub.add_parser("state", help="Get or set a world-state key")
    st.add_argument("--key", required=True)
    st.add_argument("--value", default=None)

    sub.add_parser("snap", help="Print a full world snapshot")

    rw = sub.add_parser("rewind", help="Rewind trajectory by N steps")
    rw.add_argument("--step", type=int, default=1)

    gl = sub.add_parser("globe", help="Set particle-globe coordinates for a node")
    gl.add_argument("--node", required=True)
    gl.add_argument("--lat", type=float, required=True)
    gl.add_argument("--lon", type=float, required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "set":    _cmd_set_node,
        "get":    _cmd_get_node,
        "state":  _cmd_state,
        "snap":   _cmd_snap,
        "rewind": _cmd_rewind,
        "globe":  _cmd_globe,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
