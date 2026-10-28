from __future__ import annotations

import argparse
import json
import sys

from guiml_bench.paths import GOLD_DIR, GUIML_DIR, TASKS_DIR
from guiml_bench.tasks.schema import load_tasks, validate_tasks


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="guiml-bench")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("extract", help="rebuild Carbon packs + GUIML graphs")
    sub.add_parser("validate-tasks", help="lint the task suite")
    g = sub.add_parser("grade-gold", help="grade the 15 gold files (must score high on R1/R2/R5/R6)")
    g.add_argument("--scale", default="L")
    r = sub.add_parser("run", help="run a profile")
    r.add_argument("--profile", default="smoke", choices=["smoke", "tier1", "tier2", "tier3", "demo"])
    r.add_argument("--models", default=None, help="comma-separated provider:model")
    r.add_argument("--tasks", default=None, help="comma-separated task ids")
    r.add_argument("--reps", type=int, default=None)
    r.add_argument("--concurrency", type=int, default=8)
    r.add_argument("--run-id", default=None)
    e = sub.add_parser("estimate", help="print cell count and cost for a profile")
    e.add_argument("--profile", default="tier1")
    e.add_argument("--models", default=None)
    rp = sub.add_parser("report", help="write figures + tables from a run dir")
    rp.add_argument("--run", required=True)
    hf = sub.add_parser("push-hf", help="push datasets / space files (requires huggingface_hub)")
    hf.add_argument("--repo", default="guiml-bench")
    hf.add_argument("--private", action="store_true", default=True)

    args = p.parse_args(argv)
    if args.cmd == "extract":
        from guiml.graph import write_system_graph

        print("Run: (cd carbon && npm run extract)")
        for s in "SML":
            path = write_system_graph(s)
            print("wrote", path)
        return 0
    if args.cmd == "validate-tasks":
        errors = validate_tasks()
        print(f"{len(load_tasks())} tasks in {TASKS_DIR}")
        if errors:
            print("FAIL")
            for e in errors:
                print(" -", e)
            return 1
        print("ok")
        return 0
    if args.cmd == "grade-gold":
        from guiml_bench.graders.score import grade_gold_dir

        rows = grade_gold_dir(GOLD_DIR, scale=args.scale)
        fails = []
        for row in rows:
            uw = row["unweighted"]
            # gold is allowed to miss some expected tokens (R1 recall) but must not use raw values,
            # must not hallucinate, must not use v10 names, must use a grid.
            bad = []
            if not uw["R2"]:
                bad.append("R2")
            if not uw["R5"]:
                bad.append("R5")
            if not uw["R6"]:
                bad.append("R6")
            if row["per_class"]["R1"]["raw_value_count"] > 0:
                bad.append("R1-raw")
            if bad:
                fails.append((row["task"], bad, row["gs"]))
            print(f"{row['task']} GS={row['gs']} {uw}")
        print(f"{len(rows)} gold files, {len(fails)} below bar")
        return 1 if fails else 0
    if args.cmd == "estimate":
        from guiml_bench.runner import estimate, expand

        models = args.models.split(",") if args.models else None
        cells = expand(args.profile, models=models)
        print(json.dumps(estimate(cells), indent=2))
        return 0
    if args.cmd == "run":
        from guiml_bench.runner import run_profile

        models = args.models.split(",") if args.models else None
        tasks = args.tasks.split(",") if args.tasks else None
        dest = run_profile(
            args.profile,
            models=models,
            task_ids=tasks,
            reps=args.reps,
            concurrency=args.concurrency,
            run_id=args.run_id,
        )
        print("wrote", dest)
        return 0
    if args.cmd == "report":
        from guiml_bench.stats import write_report

        write_report(args.run)
        return 0
    if args.cmd == "push-hf":
        from guiml_bench.hf_push import push

        push(args.repo, private=args.private)
        return 0
    return 2


if __name__ == "__main__":
    sys.exit(main())
