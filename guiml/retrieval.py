"""Rule-class-budgeted sub-graph retrieval."""
from __future__ import annotations

from typing import Any, Iterable

DEFAULT_BUDGETS = {"R1": 40, "R2": 25, "R3": 8, "R4": 6, "R5": 20, "R6": 8}


def retrieve_subgraph(
    graph: dict[str, Any],
    *,
    expected_components: Iterable[str] = (),
    expected_tokens: Iterable[str] = (),
    forbidden_names: Iterable[str] = (),
    budgets: dict[str, int] | None = None,
    include_lifecycle: bool = True,
) -> dict[str, Any]:
    budgets = budgets or DEFAULT_BUDGETS
    nodes = {n["id"]: n for n in graph["nodes"]}
    keep: dict[str, dict] = {}

    def take(nid: str) -> None:
        n = nodes.get(nid)
        if n:
            keep[nid] = n

    wanted_comp = {f"component:{c}" for c in expected_components}
    wanted_tok = {f"token:{t}" for t in expected_tokens}
    for nid in list(wanted_comp | wanted_tok):
        take(nid)

    by_class: dict[str, list[dict]] = {}
    for n in graph["nodes"]:
        by_class.setdefault(n.get("ruleClass", "R1"), []).append(n)

    if include_lifecycle:
        for e in graph["edges"]:
            if e["kind"] == "replaces":
                take(e["from"])
                take(e["to"])

    for rc, budget in budgets.items():
        pool = by_class.get(rc, [])
        if rc == "R5" and not include_lifecycle:
            continue
        scored = []
        for n in pool:
            score = 0
            if n["id"] in keep:
                score += 10
            if n.get("name") in set(expected_components) | set(expected_tokens) | set(forbidden_names):
                score += 8
            if n["kind"] == "rule":
                score += 5
            scored.append((score, n))
        scored.sort(key=lambda x: -x[0])
        for _, n in scored[:budget]:
            take(n["id"])

    keep_ids = set(keep)
    edges = [e for e in graph["edges"] if e["from"] in keep_ids and e["to"] in keep_ids]
    # pull replace-targets for any kept v10 token
    for e in graph["edges"]:
        if e["kind"] == "replaces" and e["from"] in keep_ids:
            take(e["to"])
            if e not in edges:
                edges.append(e)
    return {
        "kind": "system",
        "id": f"{graph.get('id', 'graph')}-sub",
        "scale": graph.get("scale"),
        "nodes": list(keep.values()),
        "edges": edges,
    }


def subgraph_to_prompt(sub: dict[str, Any]) -> str:
    """Serialize a sub-graph into a compact prompt block."""
    tokens = [n for n in sub["nodes"] if n["kind"] == "token"]
    comps = [n for n in sub["nodes"] if n["kind"] == "component"]
    rules = [n for n in sub["nodes"] if n["kind"] == "rule"]
    replaces = [e for e in sub["edges"] if e["kind"] == "replaces"]
    lines = ["# GUIML design-system sub-graph", ""]
    lines.append("## Tokens")
    for n in tokens[:80]:
        lines.append(f"- {n['name']} role={n.get('role')} status={n.get('status')} css={n.get('css')}")
    lines.append("\n## Components")
    for n in comps:
        props = ", ".join(p.get("name", "") for p in (n.get("props") or [])[:12])
        lines.append(f"- {n['name']} status={n.get('status')} props=[{props}]")
    if replaces:
        lines.append("\n## Lifecycle (v10 → v11)")
        for e in replaces:
            lines.append(f"- {e['from'].split(':')[-1]} replaces→ {e['to'].split(':')[-1]}")
    if rules:
        lines.append("\n## Usage rules")
        for n in rules:
            lines.append(f"- ({n.get('ruleClass')}) {n.get('text')}")
    return "\n".join(lines)
