from pathlib import Path

from guiml_bench.graders.score import grade_gold_dir, grade_sample
from guiml_bench.paths import GOLD_DIR, ROOT
from guiml_bench.providers.mock import VIBE, CLEAN
from guiml_bench.tasks.schema import load_tasks, validate_tasks


def test_validate_tasks():
    errors = validate_tasks()
    assert errors == []
    tasks = load_tasks()
    assert len(tasks) == 80
    assert sum(1 for t in tasks if t.trap) == 20
    assert sum(1 for t in tasks if t.gold) == 15


def test_gold_no_raw_and_no_v10():
    rows = grade_gold_dir(GOLD_DIR, scale="L")
    assert len(rows) == 15
    for row in rows:
        assert row["per_class"]["R1"]["raw_value_count"] == 0, row["task"]
        assert row["unweighted"]["R5"], row["task"]
        assert row["unweighted"]["R2"], row["task"]
        assert row["unweighted"]["R6"], row["task"]


def test_vibe_fails_r1_r2():
    task = next(t for t in load_tasks() if t.pattern == "form")
    bad = grade_sample(VIBE, task, scale="L")
    good = grade_sample(CLEAN, task, scale="L")
    assert bad["per_class"]["R1"]["raw_value_count"] > 0
    assert good["gs"] >= bad["gs"]
