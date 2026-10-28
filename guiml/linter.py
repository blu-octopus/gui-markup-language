from __future__ import annotations

import json
from typing import Any

from guiml_bench.paths import CARBON_COMPOSITION


def _walk(node: Any):
    if isinstance(node, str):
        return
    yield node
    for ch in node.get("children") or []:
        yield from _walk(ch)


def lint_instance(instance: dict[str, Any], graph: dict[str, Any]) -> list[dict[str, Any]]:
    """Deterministic R1/R2/R5 + schema diagnostics. Empty list = pass."""
    diagnostics: list[dict[str, Any]] = []
    if instance.get("kind") != "instance" or "root" not in instance:
        return [{"code": "schema", "message": "instance must have kind=instance and root"}]

    nodes = {n["id"]: n for n in graph.get("nodes", [])}
    token_names = {n["name"] for n in nodes.values() if n["kind"] == "token" and n.get("status") == "active"}
    deprecated_tokens = {n["name"] for n in nodes.values() if n["kind"] == "token" and n.get("status") in {"deprecated", "renamed", "removed"}}
    component_names = {n["name"] for n in nodes.values() if n["kind"] == "component" and n.get("status") not in {"removed", "deprecated"}}
    replaces = {e["from"].split(":")[-1]: e["to"].split(":")[-1] for e in graph.get("edges", []) if e["kind"] == "replaces"}
    composition = json.loads(CARBON_COMPOSITION.read_text(encoding="utf-8"))
    required = composition.get("requiredChildren", {})

    used_components: list[str] = []
    for node in _walk(instance["root"]):
        if not isinstance(node, dict):
            continue
        name = node.get("component")
        if not name:
            diagnostics.append({"code": "R2", "message": "tree node missing component"})
            continue
        used_components.append(name)
        if name not in component_names:
            diagnostics.append({"code": "R2", "message": f"unknown or removed component {name}", "rewrite": replaces.get(name)})
        for token in (node.get("tokens") or {}).values():
            if token in deprecated_tokens:
                diagnostics.append(
                    {
                        "code": "R5",
                        "message": f"deprecated/renamed token {token}",
                        "rewrite": replaces.get(token),
                    }
                )
            elif token not in token_names and token not in replaces:
                diagnostics.append({"code": "R1", "message": f"token {token} not in pack"})

    used_set = set(used_components)
    for parent, children in required.items():
        if parent not in used_set:
            continue
        for spec in children:
            alts = spec.split("|")
            if not any(a in used_set for a in alts):
                diagnostics.append({"code": "R2", "message": f"{parent} requires one of {alts}"})
    return diagnostics


def apply_rewrites(instance: dict[str, Any], diagnostics: list[dict[str, Any]]) -> dict[str, Any]:
    """Rewrite renamed tokens/components in place using linter rewrite hints."""
    mapping = {d["message"].split()[-1]: d["rewrite"] for d in diagnostics if d.get("rewrite")}

    def fix(node: Any) -> Any:
        if isinstance(node, str):
            return node
        name = node.get("component")
        if name in mapping:
            node = {**node, "component": mapping[name]}
        tokens = node.get("tokens") or {}
        tokens = {k: mapping.get(v, v) for k, v in tokens.items()}
        children = [fix(c) for c in (node.get("children") or [])]
        return {**node, "tokens": tokens, "children": children}

    return {**instance, "root": fix(instance["root"])}
