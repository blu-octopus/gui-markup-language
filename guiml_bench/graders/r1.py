from __future__ import annotations

import re
from typing import Any

from guiml_bench.tasks.schema import Task

HEX = re.compile(r"#[0-9A-Fa-f]{3,8}\b")
RGB = re.compile(r"\b(?:rgb|hsl)a?\(", re.I)
ARBITRARY = re.compile(r"(?:bg|text|border|w|h|p|m|gap)-\[[^\]]+\]")
CSS_VAR = re.compile(r"var\(--cds-([a-z0-9-]+)\)")
SCSS_VAR = re.compile(r"\$([a-z0-9-]+)")
INLINE_PX = re.compile(r"(?:padding|margin|gap|font-size|width|height)\s*[:=]\s*['\"]?\d+px")


def grade_r1(tsx: str, task: Task, pack: dict[str, Any]) -> dict[str, Any]:
    pack_names = {t["name"] for t in pack["tokens"]}
    used = set(CSS_VAR.findall(tsx)) | set(SCSS_VAR.findall(tsx))
    used &= pack_names | set(task.expected_tokens)
    raw_hex = HEX.findall(tsx)
    # ignore hex inside comments of source maps; still count in source
    n_raw = len(raw_hex) + len(RGB.findall(tsx)) + len(ARBITRARY.findall(tsx)) + len(INLINE_PX.findall(tsx))
    expected = set(task.expected_tokens) & pack_names
    precision = (len(used) / max(len(used) + n_raw, 1))
    recall = (len(used & expected) / max(len(expected), 1)) if expected else 1.0
    role_ok = True
    if "text-primary" in expected and "text-secondary" in expected:
        role_ok = ("text-primary" in used or "cds--type" in tsx) and (
            "text-secondary" in used or "text-helper" in used or "cds--type-label" in tsx or "text-secondary" in tsx
        )
    pass_ = n_raw == 0 and recall >= 0.3
    return {
        "pass": pass_,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "raw_value_count": n_raw,
        "used_tokens": sorted(used),
        "role_ok": role_ok,
        "details": {"hex": raw_hex[:10]},
    }
