from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field, field_validator

from guiml_bench.paths import CARBON_OUT, TASKS_DIR

RuleClass = Literal["R1", "R2", "R3", "R4", "R5", "R6"]
Scale = Literal["S", "M", "L"]
TrapKind = Literal["lexical", "lifecycle", "semantic", "a11y"]
Domain = Literal["admin", "finance", "healthcare", "devtools"]
Pattern = Literal[
    "table",
    "form",
    "kpi-grid",
    "modal",
    "shell-nav",
    "notification",
    "wizard",
    "settings",
]


class Checkpoint(BaseModel):
    id: str
    rule_class: RuleClass
    text: str
    critical: bool = False


class ForbiddenItem(BaseModel):
    kind: Literal["token", "component", "package"]
    name: str
    reason: str
    expect: str | None = None


class Task(BaseModel):
    id: str
    domain: Domain
    pattern: Pattern
    difficulty: Literal[1, 2, 3]
    trap: list[TrapKind] = Field(default_factory=list)
    prompt: str
    scales: list[Scale]
    expected_components: list[str]
    expected_tokens: list[str]
    forbidden: list[ForbiddenItem] = Field(default_factory=list)
    checkpoints: list[Checkpoint]
    gold: str | None = None  # relative path under data/gold/

    @field_validator("id")
    @classmethod
    def _id_shape(cls, v: str) -> str:
        if not re.match(r"^[a-z]{3}-\d{3}$", v):
            raise ValueError("id must look like tbl-007")
        return v

    def checkpoints_for(self, rule_class: RuleClass) -> list[Checkpoint]:
        return [c for c in self.checkpoints if c.rule_class == rule_class]


def save_task(task: Task, dest: Path | None = None) -> Path:
    dest = dest or (TASKS_DIR / f"{task.id}.yaml")
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(yaml.safe_dump(task.model_dump(), sort_keys=False, allow_unicode=True), encoding="utf-8")
    return dest


def load_task(path: Path) -> Task:
    return Task.model_validate(yaml.safe_load(path.read_text(encoding="utf-8")))


def load_tasks(directory: Path | None = None) -> list[Task]:
    directory = directory or TASKS_DIR
    files = sorted(directory.glob("*.yaml"))
    return [load_task(p) for p in files]


def catalog_names() -> set[str]:
    components = json.loads((CARBON_OUT / "components.json").read_text())
    return {c["name"] for c in components["components"]}


COMPONENT_NAME_RE = re.compile(r"\b(" + r"|".join(sorted(catalog_names(), key=len, reverse=True)) + r")\b") if (CARBON_OUT / "components.json").exists() else re.compile(r"$a")


def validate_tasks(tasks: list[Task] | None = None) -> list[str]:
    """Return a list of errors. Empty means green."""
    tasks = tasks if tasks is not None else load_tasks()
    names = catalog_names() if (CARBON_OUT / "components.json").exists() else set()
    errors: list[str] = []
    seen = set()
    trap_n = 0
    for t in tasks:
        if t.id in seen:
            errors.append(f"{t.id}: duplicate id")
        seen.add(t.id)
        if t.trap:
            trap_n += 1
        if names:
            leaked = sorted({m for m in COMPONENT_NAME_RE.findall(t.prompt) if m in names})
            # allow common English words that collide (Form, Grid, Header, Content, Tag, Table, Search, Link)
            allow = {"Form", "Grid", "Header", "Content", "Tag", "Table", "Search", "Link", "Toggle", "Select", "Column"}
            leaked = [m for m in leaked if m not in allow]
            if leaked:
                errors.append(f"{t.id}: prompt names components {leaked}")
            for c in t.expected_components:
                if c not in names:
                    errors.append(f"{t.id}: unknown expected component {c}")
        classes = {c.rule_class for c in t.checkpoints}
        for rc in ("R1", "R2", "R3", "R4", "R6"):
            if rc not in classes:
                errors.append(f"{t.id}: missing {rc} checkpoint")
        if t.trap and "lifecycle" in t.trap and "R5" not in classes:
            errors.append(f"{t.id}: lifecycle trap without R5 checkpoint")
        if "S" in t.scales and t.pattern not in {"form", "modal", "kpi-grid", "notification"}:
            # S only has 10 primitives; table/shell/wizard/settings need M+
            pass
    if tasks and trap_n / len(tasks) < 0.2:
        errors.append(f"trap share {trap_n}/{len(tasks)} is under 20%")
    return errors
