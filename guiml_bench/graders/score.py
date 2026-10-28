from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Callable

from guiml_bench.graders.r1 import grade_r1
from guiml_bench.graders.r2 import grade_r2
from guiml_bench.graders.r3 import grade_r3
from guiml_bench.graders.r4 import grade_r4
from guiml_bench.graders.r5 import grade_r5
from guiml_bench.graders.r6 import grade_r6
from guiml_bench.paths import pack_path
from guiml_bench.tasks.schema import Task

WEIGHTS = {"R1": 0.20, "R2": 0.20, "R3": 0.25, "R4": 0.15, "R5": 0.10, "R6": 0.10}


def load_pack(scale: str) -> dict[str, Any]:
    return json.loads(pack_path(scale).read_text(encoding="utf-8"))


def governance_score(per_class: dict[str, dict[str, Any]]) -> dict[str, Any]:
    r2 = per_class["R2"]
    gated = False
    reason = None
    if r2.get("compile_ok") is False:
        gated = True
        reason = "compile"
    if r2.get("hallucinated"):
        gated = True
        reason = "hallucinated_component"
    if gated:
        return {"gs": 0.0, "gated": True, "gate_reason": reason}
    gs = sum(WEIGHTS[k] * (1.0 if per_class[k].get("pass") else 0.0) for k in WEIGHTS)
    return {"gs": round(gs, 4), "gated": False, "gate_reason": None}


def grade_sample(
    tsx: str,
    task: Task,
    scale: str = "L",
    *,
    compile_ok: bool | None = None,
    runtime: dict[str, Any] | None = None,
    judge: Callable | None = None,
    pack: dict[str, Any] | None = None,
) -> dict[str, Any]:
    pack = pack or load_pack(scale)
    per = {
        "R1": grade_r1(tsx, task, pack),
        "R2": grade_r2(tsx, task, pack, compile_ok=compile_ok),
        "R3": grade_r3(tsx, task, judge=judge),
        "R4": grade_r4(tsx, task, runtime=runtime),
        "R5": grade_r5(tsx, task, pack),
        "R6": grade_r6(tsx, task, runtime=runtime),
    }
    gs = governance_score(per)
    return {
        "task": task.id,
        "scale": scale,
        "per_class": per,
        **gs,
        "unweighted": {k: bool(v.get("pass")) for k, v in per.items()},
    }


def grade_gold_dir(gold_dir: Path, scale: str = "L") -> list[dict[str, Any]]:
    from guiml_bench.tasks.schema import load_tasks

    tasks = {t.id: t for t in load_tasks() if t.gold}
    out = []
    for path in sorted(gold_dir.glob("*.tsx")):
        if path.name.startswith("_"):
            continue
        tid = path.stem
        if tid not in tasks:
            continue
        tsx = path.read_text(encoding="utf-8")
        out.append(grade_sample(tsx, tasks[tid], scale=scale, compile_ok=True))
    return out
