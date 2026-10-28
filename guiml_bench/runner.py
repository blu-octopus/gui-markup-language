from __future__ import annotations

import json
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

from guiml_bench.conditions.base import run_condition
from guiml_bench.graders.score import grade_sample
from guiml_bench.paths import RUNS_DIR
from guiml_bench.providers.registry import get_provider
from guiml_bench.tasks.schema import Task, load_tasks

PROFILES = {
    "smoke": {
        "tasks": 3,
        "conditions": ["B0", "B1", "B2", "B3", "T"],
        "scales": ["L"],
        "reps": 1,
        "models": ["mock"],
    },
    "tier1": {
        "tasks": None,
        "conditions": ["B0", "B1", "B2", "B3", "T"],
        "scales": ["L"],
        "reps": 3,
        "models": ["mistral:mistral-large-latest", "openai:gpt-4o", "anthropic:claude-sonnet-4-20250514", "hf:Qwen/Qwen2.5-Coder-32B-Instruct"],
    },
    "tier2": {
        "tasks": None,
        "conditions": ["B1", "B3", "T"],
        "scales": ["S", "M"],
        "reps": 3,
        "models": ["mistral:mistral-large-latest", "openai:gpt-4o", "anthropic:claude-sonnet-4-20250514", "hf:Qwen/Qwen2.5-Coder-32B-Instruct"],
    },
    "tier3": {
        "tasks": None,
        "conditions": ["T-lint", "T-life", "T+MoE"],
        "scales": ["L"],
        "reps": 2,
        "models": ["mistral:mistral-large-latest", "openai:gpt-4o"],
    },
    "demo": {
        "tasks": 8,
        "conditions": ["B0", "B1", "B2", "B3", "T", "T-lint", "T-life"],
        "scales": ["S", "L"],
        "reps": 2,
        "models": ["mock"],
    },
}

COST_HINT = {
    "mock": 0.0,
    "mistral": 0.02,
    "openai": 0.05,
    "anthropic": 0.06,
    "hf": 0.01,
}


@dataclass
class Cell:
    task: str
    condition: str
    scale: str
    model: str
    rep: int

    @property
    def key(self) -> str:
        return f"{self.task}__{self.condition}__{self.scale}__{self.model.replace('/', '_')}__r{self.rep}"


def expand(profile: str, *, models: list[str] | None = None, task_ids: Iterable[str] | None = None, reps: int | None = None) -> list[Cell]:
    spec = PROFILES[profile]
    tasks = load_tasks()
    if task_ids:
        want = set(task_ids)
        tasks = [t for t in tasks if t.id in want]
    elif spec["tasks"]:
        tasks = tasks[: spec["tasks"]]
    models = models or spec["models"]
    nrep = reps if reps is not None else spec["reps"]
    cells = []
    for t in tasks:
        for cond in spec["conditions"]:
            for scale in spec["scales"]:
                if scale not in t.scales:
                    continue
                for model in models:
                    for r in range(nrep):
                        cells.append(Cell(t.id, cond, scale, model, r))
    return cells


def estimate(cells: list[Cell]) -> dict[str, Any]:
    cost = 0.0
    for c in cells:
        fam = c.model.split(":")[0]
        cost += COST_HINT.get(fam, 0.04)
    return {"cells": len(cells), "est_cost_usd": round(cost, 2), "est_wall_h_at_30": round(len(cells) * 25 / 3600 / 30, 2)}


def _run_one(cell: Cell, task: Task, dest: Path) -> dict[str, Any]:
    cell_dir = dest / cell.key
    cell_dir.mkdir(parents=True, exist_ok=True)
    grade_path = cell_dir / "grades.json"
    if grade_path.exists():
        return json.loads(grade_path.read_text())
    provider = get_provider(cell.model)
    t0 = time.time()
    try:
        gen = run_condition(cell.condition, task, provider, cell.scale)
        tsx = gen["tsx"]
        (cell_dir / "output.tsx").write_text(tsx, encoding="utf-8")
        (cell_dir / "usage.json").write_text(json.dumps(gen["usage"], indent=2), encoding="utf-8")
        grades = grade_sample(tsx, task, scale=cell.scale, compile_ok=None)
        grades.update(
            {
                "condition": cell.condition,
                "model": cell.model,
                "rep": cell.rep,
                "ok": True,
                "error": None,
                "elapsed_s": time.time() - t0,
                "usage": gen["usage"],
                "meta": gen.get("meta"),
            }
        )
    except Exception as e:
        grades = {
            "task": cell.task,
            "condition": cell.condition,
            "scale": cell.scale,
            "model": cell.model,
            "rep": cell.rep,
            "ok": False,
            "error": str(e),
            "gs": 0.0,
            "gated": True,
            "gate_reason": "error",
            "elapsed_s": time.time() - t0,
        }
    grade_path.write_text(json.dumps(grades, indent=2, default=str), encoding="utf-8")
    return grades


def run_profile(
    profile: str,
    *,
    models: list[str] | None = None,
    task_ids: list[str] | None = None,
    reps: int | None = None,
    concurrency: int = 8,
    run_id: str | None = None,
) -> Path:
    cells = expand(profile, models=models, task_ids=task_ids, reps=reps)
    est = estimate(cells)
    run_id = run_id or time.strftime("%Y%m%d-%H%M%S") + f"-{profile}"
    dest = RUNS_DIR / run_id
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "manifest.json").write_text(
        json.dumps({"profile": profile, "estimate": est, "cells": [c.key for c in cells], "models": models}, indent=2),
        encoding="utf-8",
    )
    print(f"run {run_id}: {est['cells']} cells, est ${est['est_cost_usd']}, ~{est['est_wall_h_at_30']}h @30-way")
    by_id = {t.id: t for t in load_tasks()}
    results = []
    with ThreadPoolExecutor(max_workers=concurrency) as pool:
        futs = {pool.submit(_run_one, c, by_id[c.task], dest): c for c in cells}
        for i, fut in enumerate(as_completed(futs), 1):
            rec = fut.result()
            results.append(rec)
            if i % 10 == 0 or i == len(cells):
                print(f"  {i}/{len(cells)}")
    (dest / "results.json").write_text(json.dumps(results, indent=2, default=str), encoding="utf-8")
    return dest
