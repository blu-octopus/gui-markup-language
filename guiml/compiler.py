from __future__ import annotations

import json
import re
from typing import Any

from guiml_bench.paths import CARBON_COMPOSITION

_IDENT = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*$")


def _jsx_value(v: Any) -> str:
    if isinstance(v, bool):
        return "{true}" if v else "{false}"
    if isinstance(v, (int, float)):
        return "{" + str(v) + "}"
    if v is None:
        return "{undefined}"
    s = str(v)
    if s.startswith("{") and s.endswith("}"):
        return s
    return json.dumps(s)


def _render(node: Any, indent: int = 4) -> str:
    pad = " " * indent
    if isinstance(node, str):
        return pad + node
    name = node["component"]
    props = dict(node.get("props") or {})
    tokens = node.get("tokens") or {}
    if tokens:
        style_parts = []
        for css_prop, token in tokens.items():
            css_name = re.sub(r"[A-Z]", lambda m: "-" + m.group(0).lower(), css_prop)
            style_parts.append(f"{css_name}: 'var(--cds-{token})'")
        props["style"] = "{" + "{" + ", ".join(style_parts) + "}" + "}"
    prop_str = "".join(
        f" {k}" if v is True else f" {k}={_jsx_value(v)}"
        for k, v in props.items()
        if v is not False and v is not None
    )
    children = node.get("children") or []
    text = node.get("text")
    if text:
        children = [text, *children]
    if not children:
        return f"{pad}<{name}{prop_str} />"
    inner = "\n".join(_render(c, indent + 2) for c in children)
    return f"{pad}<{name}{prop_str}>\n{inner}\n{pad}</{name}>"


def compile_instance(instance: dict[str, Any]) -> str:
    """Compile a GUIML instance document to @carbon/react TSX."""
    used: list[str] = []

    def collect(n: Any) -> None:
        if isinstance(n, dict):
            used.append(n["component"])
            for c in n.get("children") or []:
                collect(c)

    collect(instance["root"])
    # only valid JS identifiers
    names = sorted({n for n in used if _IDENT.match(n)})
    imports = ",\n  ".join(names)
    tree = _render(instance["root"], 4)
    return (
        "import React from 'react';\n"
        f"import {{\n  {imports}\n}} from '@carbon/react';\n\n"
        "export default function TaskView() {\n"
        "  return (\n"
        f"{tree}\n"
        "  );\n"
        "}\n"
    )


def composition_hint() -> dict:
    return json.loads(CARBON_COMPOSITION.read_text(encoding="utf-8"))
