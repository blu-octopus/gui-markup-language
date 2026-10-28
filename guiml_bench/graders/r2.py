from __future__ import annotations

import json
import re
from typing import Any

from guiml_bench.paths import CARBON_COMPOSITION
from guiml_bench.tasks.schema import Task

IMPORT_RE = re.compile(
    r"import\s+(?:\{([^}]+)\}|(\w+))\s+from\s+['\"](@carbon/react|carbon-components-react)['\"]",
    re.S,
)
JSX_RE = re.compile(r"<([A-Z][A-Za-z0-9]*)\b")


def _imported(tsx: str) -> tuple[list[str], list[str]]:
    names: list[str] = []
    packages: list[str] = []
    for m in IMPORT_RE.finditer(tsx):
        pkg = m.group(3)
        packages.append(pkg)
        blob = m.group(1) or m.group(2) or ""
        for part in blob.split(","):
            part = part.strip()
            if not part:
                continue
            name = part.split(" as ")[-1].strip()
            if re.match(r"^[A-Z]", name):
                names.append(name)
    return names, packages


def grade_r2(tsx: str, task: Task, pack: dict[str, Any], compile_ok: bool | None = None) -> dict[str, Any]:
    catalog = {c["name"] for c in pack["components"]}
    imported, packages = _imported(tsx)
    jsx = JSX_RE.findall(tsx)
    used = sorted(set(imported) | set(jsx))
    hallucinated = [n for n in used if n not in catalog and n not in {"React", "Fragment"}]
    foreign = [p for p in packages if p != "@carbon/react"]
    composition = json.loads(CARBON_COMPOSITION.read_text(encoding="utf-8"))
    missing_children = []
    used_set = set(used)
    for parent, children in composition.get("requiredChildren", {}).items():
        if parent not in used_set:
            continue
        for spec in children:
            alts = spec.split("|")
            if not any(a in used_set for a in alts):
                missing_children.append({"parent": parent, "need": alts})
    expected_hit = [c for c in task.expected_components if c in used_set]
    used_from_catalog = [n for n in used if n in catalog]
    pass_ = (
        not hallucinated
        and not foreign
        and (compile_ok is not False)
        and not missing_children
        and (len(used_from_catalog) > 0)
    )
    return {
        "pass": bool(pass_),
        "compile_ok": compile_ok,
        "hallucinated": hallucinated,
        "foreign_packages": foreign,
        "missing_children": missing_children,
        "used_components": used,
        "expected_hit": expected_hit,
        "expected_recall": round(len(expected_hit) / max(len(task.expected_components), 1), 4),
    }
