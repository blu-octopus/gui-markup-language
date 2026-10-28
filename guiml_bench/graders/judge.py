"""LLM-as-judge for R3. Judge provider must differ from the generator."""
from __future__ import annotations

import json
import math
from collections import Counter
from typing import Any, Protocol

from guiml_bench.tasks.schema import Task

JUDGE_PROMPT = """You are grading generated React (@carbon/react) UI code against binary design-system usage checkpoints.
Return JSON only: {{"checkpoints": [{{"id": "...", "pass": true, "rationale": "..."}}]}}
Do not reward visual prettiness. Apply each checkpoint literally.

Task prompt:
{prompt}

Checkpoints:
{checkpoints}

Code:
```tsx
{code}
```
"""


class Completer(Protocol):
    def complete(self, prompt: str, *, json_mode: bool = False) -> str: ...


def judge_r3(tsx: str, task: Task, completer: Completer) -> dict[str, Any]:
    cps = task.checkpoints_for("R3")
    listing = "\n".join(f"- {c.id}: {c.text} (critical={c.critical})" for c in cps)
    prompt = JUDGE_PROMPT.format(prompt=task.prompt, checkpoints=listing, code=tsx[:12000])
    raw = completer.complete(prompt, json_mode=True)
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        data = json.loads(raw[start : end + 1]) if start >= 0 else {"checkpoints": []}
    by_id = {c["id"]: c for c in data.get("checkpoints", []) if "id" in c}
    results = []
    for c in cps:
        hit = by_id.get(c.id, {})
        results.append(
            {
                "id": c.id,
                "pass": bool(hit.get("pass", False)),
                "critical": c.critical,
                "rationale": hit.get("rationale", ""),
                "method": "llm-judge",
            }
        )
    n = len(results) or 1
    rate = sum(1 for r in results if r["pass"]) / n
    crit_fail = any(r["critical"] and not r["pass"] for r in results)
    return {"pass": (not crit_fail) and rate >= 0.5, "checkpoint_rate": round(rate, 4), "checkpoints": results}


def cohens_kappa(a: list[bool], b: list[bool]) -> float:
    if not a or len(a) != len(b):
        return float("nan")
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    ca, cb = Counter(a), Counter(b)
    pe = sum((ca[k] / n) * (cb[k] / n) for k in {True, False})
    if pe == 1:
        return 1.0
    return (po - pe) / (1 - pe)


def flag_low_kappa(items: list[dict[str, Any]], threshold: float = 0.6) -> list[str]:
    """items have keys checkpoint_id, rater_a, rater_b (bools)."""
    by = {}
    for it in items:
        by.setdefault(it["checkpoint_id"], {"a": [], "b": []})
        by[it["checkpoint_id"]]["a"].append(bool(it["rater_a"]))
        by[it["checkpoint_id"]]["b"].append(bool(it["rater_b"]))
    flagged = []
    for cid, ab in by.items():
        k = cohens_kappa(ab["a"], ab["b"])
        if k < threshold or math.isnan(k):
            flagged.append(cid)
    return flagged
