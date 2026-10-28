from __future__ import annotations

import re
from typing import Any

from guiml_bench.tasks.schema import Task

WEIGHT = {"critical": 4, "serious": 3, "moderate": 2, "minor": 1}


def _static_a11y(tsx: str) -> dict[str, Any]:
    inputs = len(re.findall(r"<TextInput|<NumberInput|<TextArea|<Search|<PasswordInput", tsx))
    labelled = len(re.findall(r"labelText=|aria-label=|iconDescription=", tsx))
    icon_only = "hasIconOnly" in tsx
    icon_labelled = (not icon_only) or ("iconDescription=" in tsx or "aria-label=" in tsx)
    return {
        "inputs": inputs,
        "labelled": labelled,
        "icon_labelled": icon_labelled,
        "static_pass": icon_labelled and (inputs == 0 or labelled >= inputs),
    }


def grade_r4(tsx: str, task: Task, runtime: dict[str, Any] | None = None) -> dict[str, Any]:
    static = _static_a11y(tsx)
    wvs = None
    ir = None
    runtime_ran = False
    if runtime and "violations" in runtime:
        runtime_ran = True
        wvs = 0
        serious = 0
        for v in runtime["violations"]:
            w = WEIGHT.get(str(v.get("impact", "minor")).lower(), 1)
            nodes = int(v.get("nodes", 1))
            wvs += w * nodes
            if w >= 3:
                serious += 1
        ir = serious > 0
    pass_ = static["static_pass"]
    if runtime_ran:
        pass_ = pass_ and not ir
    return {
        "pass": pass_,
        "wvs": wvs,
        "inaccessible": ir,
        "runtime": runtime_ran,
        **static,
    }
