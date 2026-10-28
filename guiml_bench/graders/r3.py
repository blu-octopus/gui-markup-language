from __future__ import annotations

import json
import re
from typing import Any, Callable

from guiml_bench.tasks.schema import Task

JudgeFn = Callable[[str, Task], dict[str, Any]]


def _heuristic_r3(tsx: str, task: Task) -> dict[str, Any]:
    """Deterministic stand-in used when no LLM judge is configured.

    Not a substitute for the paper's judge, but lets the pipeline run and
    gives a conservative lower bound. Each R3 checkpoint is mapped to a
    cheap structural proxy.
    """
    results = []
    n_primary = len(re.findall(r'kind=["\']primary["\']', tsx))
    n_danger = len(re.findall(r'kind=["\']danger', tsx)) + tsx.count("danger\n") + tsx.count("danger ")
    has_tag = "<Tag" in tsx
    has_btn = "<Button" in tsx
    has_modal = "<Modal" in tsx
    has_notif = "Notification" in tsx
    for cp in task.checkpoints_for("R3"):
        passed = True
        if cp.id in {"one-primary", "one-primary"}:
            passed = n_primary <= 1
        elif cp.id in {"status-as-tag", "resist-status-button"}:
            passed = has_tag and not re.search(r"status.*<Button", tsx, re.I | re.S)
        elif cp.id in {"danger-irreversible", "danger-last", "danger-zone"}:
            passed = n_danger >= 1 or "danger" in tsx
        elif cp.id in {"nonblocking", "resist-modal"}:
            passed = has_notif and (not has_modal or task.pattern == "modal")
            if "resist-modal" in cp.id or cp.id == "nonblocking":
                passed = has_notif and not has_modal
        elif cp.id == "validation-inline":
            passed = "invalid" in tsx or "invalidText" in tsx or has_notif
        elif cp.id == "nav-semantics":
            passed = "SideNav" in tsx
        elif cp.id == "kind-match":
            passed = "kind=\"success\"" in tsx or "kind='success'" in tsx
        elif cp.id == "hierarchy":
            passed = "heading" in tsx or "text-primary" in tsx
        results.append({"id": cp.id, "pass": bool(passed), "critical": cp.critical, "method": "heuristic"})
    n = len(results) or 1
    rate = sum(1 for r in results if r["pass"]) / n
    crit_fail = any(r["critical"] and not r["pass"] for r in results)
    return {"pass": (not crit_fail) and rate >= 0.5, "checkpoint_rate": round(rate, 4), "checkpoints": results}


def grade_r3(tsx: str, task: Task, judge: JudgeFn | None = None) -> dict[str, Any]:
    if judge is None:
        return _heuristic_r3(tsx, task)
    raw = judge(tsx, task)
    return raw
