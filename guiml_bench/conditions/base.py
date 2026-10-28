from __future__ import annotations

import json
from typing import Any

from guiml_bench.paths import pack_path
from guiml_bench.providers.base import Message, Provider
from guiml_bench.tasks.schema import Task

SYSTEM = (
    "You are a front-end engineer. Produce a single React function component named TaskView "
    "using @carbon/react. Return only TSX, no markdown fences."
)


def load_pack(scale: str) -> dict[str, Any]:
    return json.loads(pack_path(scale).read_text(encoding="utf-8"))


def extract_tsx(text: str) -> str:
    text = text.strip()
    if text.startswith("```"):
        text = text.split("\n", 1)[-1]
        if text.endswith("```"):
            text = text[: text.rfind("```")]
    return text.strip()


def pack_markdown(pack: dict[str, Any]) -> str:
    lines = ["# Design system", "", "## Tokens"]
    for t in pack["tokens"]:
        lines.append(f"- `{t['name']}` role={t.get('role')} css={t.get('css')} value={t.get('value')}")
    lines.append("\n## Components")
    for c in pack["components"]:
        props = ", ".join(p.get("name", "") for p in (c.get("props") or [])[:10])
        lines.append(f"- `{c['name']}` {c.get('status')} props=[{props}]")
    life = pack.get("lifecycle") or {}
    if life.get("forbiddenV10Names"):
        lines.append("\n## Do not use these v10 names")
        lines.append(", ".join(life["forbiddenV10Names"][:80]))
    return "\n".join(lines)


def pack_json_dump(pack: dict[str, Any]) -> str:
    slim = {
        "tokens": [{"name": t["name"], "role": t.get("role"), "css": t.get("css")} for t in pack["tokens"]],
        "components": [{"name": c["name"], "status": c.get("status")} for c in pack["components"]],
        "lifecycle": {
            "forbiddenV10Names": (pack.get("lifecycle") or {}).get("forbiddenV10Names", [])[:80],
            "renameMap": dict(list(((pack.get("lifecycle") or {}).get("renameMap") or {}).items())[:80]),
        },
    }
    return json.dumps(slim)


def run_b0(task: Task, provider: Provider, pack: dict[str, Any]) -> tuple[str, Any]:
    msgs = [
        Message("system", SYSTEM + "\nCONDITION=B0"),
        Message("user", "Use @carbon/react if you like.\n\n" + task.prompt),
    ]
    text, usage, _ = provider.complete(msgs)
    return extract_tsx(text), usage


def run_b1(task: Task, provider: Provider, pack: dict[str, Any]) -> tuple[str, Any]:
    msgs = [
        Message("system", SYSTEM + "\nCONDITION=B1\n\n" + pack_markdown(pack)),
        Message("user", task.prompt),
    ]
    text, usage, _ = provider.complete(msgs)
    return extract_tsx(text), usage


def run_b2(task: Task, provider: Provider, pack: dict[str, Any]) -> tuple[str, Any]:
    msgs = [
        Message("system", SYSTEM + "\nCONDITION=B2\n\nThe design system as JSON:\n" + pack_json_dump(pack)),
        Message("user", task.prompt),
    ]
    text, usage, _ = provider.complete(msgs)
    return extract_tsx(text), usage


def run_b3(task: Task, provider: Provider, pack: dict[str, Any]) -> tuple[str, Any]:
    tools = [
        {"name": "search_components", "description": "Search the catalog", "parameters": {"type": "object", "properties": {"query": {"type": "string"}}}},
        {"name": "get_component", "description": "Get one component", "parameters": {"type": "object", "properties": {"name": {"type": "string"}}}},
        {"name": "get_tokens", "description": "Tokens by category/role", "parameters": {"type": "object", "properties": {"role": {"type": "string"}}}},
    ]
    msgs = [
        Message("system", SYSTEM + "\nCONDITION=B3\nYou may call tools to inspect the design system catalog."),
        Message("user", task.prompt),
    ]
    text, usage, calls = provider.complete(msgs, tools=tools)
    if calls:
        # one round of tool results
        results = []
        comps = {c["name"]: c for c in pack["components"]}
        toks = pack["tokens"]
        for call in calls:
            name = call.get("name")
            arg = call.get("arguments") or {}
            if isinstance(arg, str):
                try:
                    arg = json.loads(arg)
                except json.JSONDecodeError:
                    arg = {}
            if name == "search_components":
                q = str(arg.get("query", "")).lower()
                hits = [c["name"] for c in pack["components"] if q in c["name"].lower()][:12]
                results.append(json.dumps(hits))
            elif name == "get_component":
                results.append(json.dumps(comps.get(arg.get("name"), {})))
            elif name == "get_tokens":
                role = str(arg.get("role", ""))
                results.append(json.dumps([t for t in toks if t.get("role") == role][:30]))
        msgs.append(Message("user", "Tool results:\n" + "\n".join(results) + "\nNow emit the TSX."))
        text, usage2, _ = provider.complete(msgs)
        usage.input_tokens += usage2.input_tokens
        usage.output_tokens += usage2.output_tokens
        usage.latency_s += usage2.latency_s
        if usage.cost_usd is not None and usage2.cost_usd is not None:
            usage.cost_usd += usage2.cost_usd
    return extract_tsx(text), usage


def run_treatment(
    task: Task,
    provider: Provider,
    pack: dict[str, Any],
    *,
    lint: bool = True,
    lifecycle: bool = True,
    moe: bool = False,
) -> tuple[str, Any, dict[str, Any]]:
    from guiml.compiler import compile_instance
    from guiml.graph import build_system_graph
    from guiml.linter import apply_rewrites, lint_instance
    from guiml.retrieval import retrieve_subgraph, subgraph_to_prompt

    graph = build_system_graph(pack["id"])
    sub = retrieve_subgraph(
        graph,
        expected_components=task.expected_components,
        expected_tokens=task.expected_tokens,
        forbidden_names=[f.name for f in task.forbidden],
        include_lifecycle=lifecycle,
    )
    hint = "T+MoE" if moe else "T-lint" if not lint else "T-life" if not lifecycle else "T"
    schema_hint = (
        "Emit a GUIML instance JSON: {\"kind\":\"instance\",\"root\":"
        "{\"component\":\"Grid\",\"props\":{},\"tokens\":{},\"children\":[...]}} "
        "Every style value must be a token name in the `tokens` map."
    )
    if moe:
        schema_hint += " Think in experts: layout, tokens, accessibility, then merge."
    msgs = [
        Message("system", SYSTEM + f"\nCONDITION={hint}\n" + schema_hint + "\n\n" + subgraph_to_prompt(sub)),
        Message("user", task.prompt + "\nReturn JSON only."),
    ]
    text, usage, _ = provider.complete(msgs, json_mode=True)
    meta: dict[str, Any] = {"repair_turns": 0, "diagnostics": []}
    try:
        instance = json.loads(extract_tsx(text))
        if instance.get("kind") != "instance":
            raise ValueError("not instance")
    except Exception:
        # mock and some models emit TSX anyway
        if "export default" in text or "<" in text:
            return extract_tsx(text), usage, meta
        instance = {
            "kind": "instance",
            "root": {"component": "Grid", "children": [{"component": "Column", "children": ["Failed to parse"]}]},
        }
    if lint:
        for _ in range(3):
            diags = lint_instance(instance, sub)
            meta["diagnostics"] = diags
            if not diags:
                break
            instance = apply_rewrites(instance, diags)
            remaining = lint_instance(instance, sub)
            if not remaining:
                break
            meta["repair_turns"] += 1
            msgs.append(Message("user", "Linter diagnostics (fix and re-emit JSON):\n" + json.dumps(remaining)))
            text, usage2, _ = provider.complete(msgs, json_mode=True)
            usage.input_tokens += usage2.input_tokens
            usage.output_tokens += usage2.output_tokens
            usage.latency_s += usage2.latency_s
            try:
                instance = json.loads(extract_tsx(text))
            except Exception:
                break
            if meta["repair_turns"] >= 2:
                break
    try:
        tsx = compile_instance(instance)
    except Exception:
        tsx = extract_tsx(text)
    return tsx, usage, meta


def run_condition(
    condition: str,
    task: Task,
    provider: Provider,
    scale: str,
) -> dict[str, Any]:
    pack = load_pack(scale)
    meta: dict[str, Any] = {}
    if condition == "B0":
        tsx, usage = run_b0(task, provider, pack)
    elif condition == "B1":
        tsx, usage = run_b1(task, provider, pack)
    elif condition == "B2":
        tsx, usage = run_b2(task, provider, pack)
    elif condition == "B3":
        tsx, usage = run_b3(task, provider, pack)
    elif condition in {"T", "T-lint", "T-life", "T+MoE"}:
        tsx, usage, meta = run_treatment(
            task,
            provider,
            pack,
            lint=condition != "T-lint",
            lifecycle=condition != "T-life",
            moe=condition == "T+MoE",
        )
    else:
        raise KeyError(condition)
    return {"tsx": tsx, "usage": usage.__dict__, "meta": meta, "condition": condition, "scale": scale}
