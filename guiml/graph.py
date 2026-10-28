from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from guiml_bench.paths import CARBON_COMPOSITION, CARBON_OUT, GUIML_DIR


def _load(name: str) -> dict:
    return json.loads((CARBON_OUT / name).read_text(encoding="utf-8"))


def build_system_graph(scale: str = "L") -> dict[str, Any]:
    pack = json.loads((CARBON_OUT / f"pack-{scale.upper()}.json").read_text(encoding="utf-8"))
    lifecycle = _load("lifecycle.json")
    composition = json.loads(CARBON_COMPOSITION.read_text(encoding="utf-8"))
    nodes: list[dict] = []
    edges: list[dict] = []
    seen: set[str] = set()

    def add_node(n: dict) -> None:
        if n["id"] in seen:
            return
        seen.add(n["id"])
        nodes.append(n)

    for t in pack["tokens"]:
        add_node(
            {
                "id": f"token:{t['name']}",
                "kind": "token",
                "name": t["name"],
                "ruleClass": "R1",
                "status": t.get("status", "active"),
                "role": t.get("role"),
                "css": t.get("css"),
                "scss": t.get("scss"),
            }
        )
    for v10, targets in lifecycle.get("renameMap", {}).items():
        add_node(
            {
                "id": f"token:{v10}",
                "kind": "token",
                "name": v10,
                "ruleClass": "R5",
                "status": "renamed" if targets else "deprecated",
            }
        )
        for v11 in targets:
            edges.append({"from": f"token:{v10}", "to": f"token:{v11}", "kind": "replaces"})

    for c in pack["components"]:
        cid = f"component:{c['name']}"
        add_node(
            {
                "id": cid,
                "kind": "component",
                "name": c["name"],
                "ruleClass": "R2",
                "status": c.get("status", "active"),
                "props": c.get("props") or [],
            }
        )
        for child in composition.get("requiredChildren", {}).get(c["name"], []):
            for part in child.split("|"):
                edges.append({"from": cid, "to": f"component:{part}", "kind": "dependsOn"})

    for rem in lifecycle.get("removedComponents", []):
        add_node(
            {
                "id": f"component:{rem}",
                "kind": "component",
                "name": rem,
                "ruleClass": "R5",
                "status": "removed",
            }
        )

    for rule in composition.get("semanticRules", []):
        rid = f"rule:{rule['id']}"
        add_node(
            {
                "id": rid,
                "kind": "rule",
                "name": rule["id"],
                "ruleClass": rule["ruleClass"],
                "status": "active",
                "text": rule["text"],
            }
        )
        for c in pack["components"]:
            if c["name"] in {"Button", "Modal", "Tag", "InlineNotification", "ToastNotification"}:
                edges.append({"from": rid, "to": f"component:{c['name']}", "kind": "constrains"})

    graph = {
        "kind": "system",
        "id": f"carbon-v11-{scale.upper()}",
        "source": pack.get("source"),
        "scale": scale.upper(),
        "nodes": nodes,
        "edges": edges,
    }
    return graph


def write_system_graph(scale: str = "L", dest: Path | None = None) -> Path:
    graph = build_system_graph(scale)
    dest = dest or (GUIML_DIR / f"carbon-{scale.lower()}.guiml.json")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(graph, indent=2), encoding="utf-8")
    return dest


def load_system_graph(path: Path | None = None) -> dict[str, Any]:
    path = path or (GUIML_DIR / "carbon-l.guiml.json")
    if not path.exists():
        write_system_graph("L", path)
    return json.loads(path.read_text(encoding="utf-8"))
