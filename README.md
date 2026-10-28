# GUIML-Bench

A public benchmark for **design-system-governed UI generation**, and **GUIML**, a rule-typed representation of a design system that LLM agents can be governed by.

Install: `pip install -e .`

## Why

Design systems are formal rule systems. LLMs generate UIs from learned prototypes. Registry-grounded agents reach ~95% on component-level checklists (Cha & Jo, CHI EA 2026), but that number is measured on toy systems, hides which *kinds* of rules fail, and never tests whether agents respect a system's evolution.

GUIML-Bench measures compliance per **rule class** on IBM Carbon v11, across three **design-system scales**, with **lifecycle trap** tasks from Carbon's own v10→v11 migration table.

| Class | Governs | Grader |
| --- | --- | --- |
| R1 Lexical/token | values resolve to tokens; correct token role | AST, precision/recall vs expected set |
| R2 Structural/API | real components, real props, required composition | catalog check, `tsc` |
| R3 Semantic/usage | right component for the intent | LLM judge ≠ generator, κ-validated |
| R4 Accessibility | WCAG 2.1 AA at 1440/375 | Playwright + axe-core, WVS |
| R5 Lifecycle | no deprecated/renamed names; correct v11 target | migration-table lookup |
| R6 Layout/responsive | Carbon grid; no overlap/overflow at 375 | Playwright bounding boxes |

Conditions: **B0** none, **B1** prose `design.md`, **B2** JSON dump, **B3** registry tool-calls, **T** GUIML. Ablations: `T-lint`, `T-life`, `T+MoE`.

## Quick start (no API keys)

```bash
python -m guiml_bench.cli validate-tasks
python -m guiml_bench.cli grade-gold
python -m guiml_bench.cli run --profile smoke --models mock
python -m guiml_bench.cli run --profile demo --models mock --run-id demo-mock
python -m guiml_bench.cli report --run demo-mock
```

Paid run day (Tier 1 ≈ 4,800 cells, ~$170, ~1h at 30-way concurrency): see [RUN.md](RUN.md).

## Layout

```
guiml_bench/   Python package (CLI, conditions, providers, graders, runner, stats)
guiml/         JSON Schema, Carbon graphs, retrieval, linter, compiler
carbon/        extract scripts → tokens, components, lifecycle, S/M/L packs
data/tasks     80 intent-level YAML tasks (20 traps, 15 gold)
data/gold      gold @carbon/react files
fixture/       Vite + React render target
grader-node/   tsc / Playwright / axe sidecar
space/         Gradio leaderboard
paper/         IEEEtran draft + CHI workshop position paper
runs/          per-cell artifacts
docs/taxonomy.md
```

## Hugging Face

Staged export: `python -m guiml_bench.cli push-hf --repo YOURUSER/guiml-bench` (requires `hf auth login`).

Planned Hub repos:

- `YOURUSER/guiml-bench-tasks` — `data/tasks` + `dist/hf/tasks.jsonl`
- `YOURUSER/guiml-bench-carbon` — packs + GUIML graphs
- `YOURUSER/guiml-bench-results` — `runs/*/results.json`
- Space from `space/` (Gradio leaderboard)

## Author

Daphne Cheng, CS 8903, Georgia Tech. Advisor: Prof. Vijay K. Madisetti.
