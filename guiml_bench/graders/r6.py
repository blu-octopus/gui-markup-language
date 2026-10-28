from __future__ import annotations

from typing import Any

from guiml_bench.tasks.schema import Task


def grade_r6(tsx: str, task: Task, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    grid_used = "<Grid" in tsx or "Grid " in tsx
    column_used = "<Column" in tsx
    overlay = "<Modal" in tsx or "<ComposedModal" in tsx or "<InlineNotification" in tsx
    absolute = "position: 'absolute'" in tsx or 'position: "absolute"' in tsx or "position:absolute" in tsx.replace(" ", "")
    overlap = None
    overflow = None
    runtime_ran = False
    if runtime:
        runtime_ran = True
        overlap = runtime.get("overlap_375", 0)
        overflow = runtime.get("overflow_375", False)
    layout_ok = grid_used or (task.pattern in {"modal", "notification"} and overlay)
    pass_ = layout_ok and not absolute
    if runtime_ran:
        pass_ = pass_ and (overlap == 0) and (not overflow)
    return {
        "pass": pass_,
        "grid_used": grid_used,
        "column_used": column_used,
        "absolute_position": absolute,
        "overlap_375": overlap,
        "overflow_375": overflow,
        "runtime": runtime_ran,
    }
