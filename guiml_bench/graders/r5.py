from __future__ import annotations

import re
from typing import Any

from guiml_bench.tasks.schema import Task

V10_PKG = re.compile(r"from\s+['\"]carbon-components-react['\"]")


def grade_r5(tsx: str, task: Task, pack: dict[str, Any]) -> dict[str, Any]:
    lifecycle = pack.get("lifecycle") or {}
    forbidden = set(lifecycle.get("forbiddenV10Names") or [])
    rename = lifecycle.get("renameMap") or {}
    removed = set(lifecycle.get("removedComponents") or [])
    task_forbidden = [f.name for f in task.forbidden]
    # Token mentions: CSS/SCSS variables, and quoted names inside style/color context.
    # Do not scan all quoted JSX enums (`kind="danger"` is valid v11 Button API).
    css = set(re.findall(r"--cds-([a-z0-9-]+)", tsx))
    scss = set(re.findall(r"\$([a-z0-9-]+)", tsx))
    style_quoted = set(
        re.findall(
            r"(?:color|background|border|fill|stroke|outline)\s*[:=]\s*['\"]([a-z0-9-]+)['\"]",
            tsx,
            flags=re.I,
        )
    )
    used_names = css | scss | (style_quoted & (forbidden | set(rename) | set(task_forbidden)))

    deprecated_used = sorted((used_names & forbidden) | (used_names & removed))
    task_hits = [n for n in task_forbidden if n in used_names]
    rename_ok = []
    for item in task.forbidden:
        if item.expect:
            rename_ok.append(
                {"from": item.name, "to": item.expect, "used_target": item.expect in tsx}
            )
    has_v10_pkg = bool(V10_PKG.search(tsx))
    pass_ = not deprecated_used and not task_hits and not has_v10_pkg
    return {
        "pass": pass_,
        "deprecated_used": deprecated_used,
        "task_forbidden_hits": task_hits,
        "rename_correctness": rename_ok,
        "v10_package": has_v10_pkg,
    }
