#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
prompt_template.py — Prompt Template Manager
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

Industry capability: structured prompt template management (LangChain-style).
MRL extension: templates are versioned and stamped with origin_signature;
               rendered prompts are traceable to a named template id.

A *PromptTemplate* declares a text skeleton with ``{variable}`` placeholders.
The TemplateRegistry manages a named collection and renders on demand.

Usage (library)
---------------
    from prompt_template import TemplateRegistry

    reg = TemplateRegistry()
    reg.add("greet", "Hello, {name}! You are a {role}.")

    rendered = reg.render("greet", {"name": "FlowAgent", "role": "kernel"})
    print(rendered)   # Hello, FlowAgent! You are a kernel.

CLI
---
    python 09_workflow/prompt_template.py add  --id greet --text "Hello, {name}!"
    python 09_workflow/prompt_template.py render --id greet --vars '{"name":"MRL"}'
    python 09_workflow/prompt_template.py list
    python 09_workflow/prompt_template.py show --id greet
"""

from __future__ import annotations

import argparse
import json
import pathlib
import re
import time
from typing import Any, Dict, List, Optional

ORIGIN_SIGNATURE = "MrLiouWord"
TEMPLATE_VERSION = "1.0"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_STORE = _REPO_ROOT / "data" / "prompt_templates.json"

_VAR_RE = re.compile(r"\{(\w+)\}")


# ─── PromptTemplate ───────────────────────────────────────────────────────────

class PromptTemplate:
    """
    A single versioned prompt template.

    Attributes
    ----------
    id          : unique template name
    text        : raw template text with ``{variable}`` placeholders
    description : human-readable purpose string
    variables   : set of declared variable names extracted from text
    version     : integer counter, incremented on update
    """

    def __init__(
        self,
        template_id: str,
        text: str,
        description: str = "",
        version: int = 1,
        created_at_ms: Optional[int] = None,
    ) -> None:
        self.id = template_id
        self.text = text
        self.description = description
        self.version = version
        self.created_at_ms = created_at_ms or int(time.time() * 1000)
        self.variables: List[str] = sorted(set(_VAR_RE.findall(text)))

    def render(self, variables: Dict[str, Any]) -> str:
        """
        Substitute *variables* into the template text.

        Raises
        ------
        KeyError if a placeholder in the template has no matching key in
        *variables*.
        """
        missing = [v for v in self.variables if v not in variables]
        if missing:
            raise KeyError(
                f"template '{self.id}': missing variable(s): {missing}"
            )
        result = self.text
        for k, v in variables.items():
            result = result.replace(f"{{{k}}}", str(v))
        return result

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "text": self.text,
            "description": self.description,
            "version": self.version,
            "created_at_ms": self.created_at_ms,
            "variables": self.variables,
            "origin_signature": ORIGIN_SIGNATURE,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "PromptTemplate":
        return cls(
            template_id=d["id"],
            text=d["text"],
            description=d.get("description", ""),
            version=d.get("version", 1),
            created_at_ms=d.get("created_at_ms"),
        )


# ─── TemplateRegistry ────────────────────────────────────────────────────────

class TemplateRegistry:
    """
    Persisted collection of named PromptTemplates.

    All mutations are persisted to *store_path* (JSON) so they survive
    between process restarts.
    """

    def __init__(self, store_path: pathlib.Path = _DEFAULT_STORE) -> None:
        self._path = pathlib.Path(store_path)
        self._templates: Dict[str, PromptTemplate] = {}
        self._load()

    # ── Persistence ───────────────────────────────────────────────────────────

    def _load(self) -> None:
        if self._path.exists():
            with self._path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            for d in data.get("templates", []):
                t = PromptTemplate.from_dict(d)
                self._templates[t.id] = t

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "template_version": TEMPLATE_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "total": len(self._templates),
            "templates": [t.to_dict() for t in self._templates.values()],
        }
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(payload, f, ensure_ascii=False, indent=2)

    # ── CRUD ──────────────────────────────────────────────────────────────────

    def add(
        self,
        template_id: str,
        text: str,
        description: str = "",
    ) -> PromptTemplate:
        """Add a new template or replace an existing one (bumps version)."""
        existing = self._templates.get(template_id)
        version = (existing.version + 1) if existing else 1
        t = PromptTemplate(template_id, text, description, version=version)
        self._templates[template_id] = t
        self._save()
        return t

    def remove(self, template_id: str) -> bool:
        if template_id in self._templates:
            del self._templates[template_id]
            self._save()
            return True
        return False

    def get(self, template_id: str) -> Optional[PromptTemplate]:
        return self._templates.get(template_id)

    def list_ids(self) -> List[str]:
        return sorted(self._templates.keys())

    # ── Render ────────────────────────────────────────────────────────────────

    def render(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Render a named template.  Raises KeyError if not found."""
        t = self._templates.get(template_id)
        if t is None:
            raise KeyError(f"template not found: '{template_id}'")
        return t.render(variables or {})

    def render_record(
        self,
        template_id: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Render and return a full trace-compatible record::

            {
              "template_id":      <str>,
              "variables":        <dict>,
              "rendered":         <str>,
              "rendered_at_ms":   <int>,
              "origin_signature": "MrLiouWord",
            }
        """
        rendered = self.render(template_id, variables)
        return {
            "template_id": template_id,
            "variables": variables or {},
            "rendered": rendered,
            "rendered_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def __len__(self) -> int:
        return len(self._templates)


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_add(args: argparse.Namespace) -> None:
    reg = TemplateRegistry()
    t = reg.add(args.id, args.text, args.desc or "")
    print(
        f"✅ Template '{t.id}' v{t.version} added  "
        f"variables={t.variables}  total={len(reg)}"
    )


def _cmd_render(args: argparse.Namespace) -> None:
    reg = TemplateRegistry()
    variables = json.loads(args.vars) if args.vars else {}
    rec = reg.render_record(args.id, variables)
    print(rec["rendered"])


def _cmd_list(_args: argparse.Namespace) -> None:
    reg = TemplateRegistry()
    ids = reg.list_ids()
    print(f"{len(ids)} template(s):")
    for tid in ids:
        t = reg.get(tid)
        if t is None:
            continue
        print(f"  {tid}  v{t.version}  vars={t.variables}")


def _cmd_show(args: argparse.Namespace) -> None:
    reg = TemplateRegistry()
    t = reg.get(args.id)
    if t is None:
        print(f"Template not found: '{args.id}'")
    else:
        print(json.dumps(t.to_dict(), ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="PromptTemplate — template manager")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add / update a template")
    a.add_argument("--id", required=True)
    a.add_argument("--text", required=True)
    a.add_argument("--desc", default="")

    r = sub.add_parser("render", help="Render a template with variables")
    r.add_argument("--id", required=True)
    r.add_argument("--vars", default="", help="JSON variable dict")

    sub.add_parser("list", help="List all templates")

    s = sub.add_parser("show", help="Show template details")
    s.add_argument("--id", required=True)

    return p


def main() -> None:
    parser = _build_argparser()
    args = parser.parse_args()
    dispatch = {
        "add":    _cmd_add,
        "render": _cmd_render,
        "list":   _cmd_list,
        "show":   _cmd_show,
    }
    dispatch[args.cmd](args)


if __name__ == "__main__":
    main()
