# Roadmap

Project: GUIML-Bench + GUIML. Framing: benchmark-first; GUIML is the treatment. Details in `context/`.
Constraint: all experiment generations must complete inside a single one-day run window. Everything before that day is build and validation; everything after is analysis and writing.

Status key: [ ] not started · [~] in progress · [x] done

---

## Phase 0 — Decide and document (done 2026-10-28)
- [x] Literature check; identify overlap with Cha & Jo 2026, open-design-system-bench, Portal UX Agent
- [x] Choose benchmark-first framing; MoE becomes ablation
- [x] Rewrite `context/*.md` to the new framing
- [ ] Confirm venue with advisor (IEEE Access per template vs HCI/SE alternate)
- [ ] Confirm model list and budget ceiling with advisor

## Phase 1 — Carbon extraction and scale packs
- [x] Pin `@carbon/themes` 11.84 / `@carbon/react` 1.119 via npm (no full Carbon monorepo clone needed)
- [x] Extract theme tokens, type/layout/spacing, component tokens → `carbon/out/tokens.json` (414)
- [x] Extract `@carbon/react` public API via react-docgen-typescript → `carbon/out/components.json` (256)
- [x] Parse vendored `docs/migration/v11.md` → `carbon/out/lifecycle.json` (145 token rows, 90 v10 names)
- [x] Build S/M/L packs; L ⊇ M ⊇ S (50/10, 275/76, 414/220)
- [x] GUIML graphs `guiml/carbon-{s,m,l}.guiml.json`
- Exit: `python -m guiml_bench.cli extract` from a clean checkout (after `cd carbon && npm install && npm run extract`)

## Phase 2 — Taxonomy and tasks
- [x] Write `docs/taxonomy.md`
- [x] Task YAML schema + `validate-tasks`
- [x] 80 tasks, 20 traps (25%)
- [x] Per-task checkpoints, expected/forbidden, scales
- [x] 15 gold React files
- [ ] Two human raters for R3 κ (paper-time; protocol in `graders/judge.py`)
- Exit: `validate-tasks` green; `grade-gold` green on R2/R5/R6

## Phase 3 — Graders
- [x] Fixture app (Vite + React + `@carbon/react`)
- [x] Node sidecar (`grader-node/index.mjs`) for tsc + optional Playwright/axe
- [x] Python graders R1–R6 + Governance Score
- [x] LLM judge prompt + Cohen's κ helpers; heuristic fallback when no judge key
- [x] Gold validation: R2/R5/R6 pass, zero raw hex (R1 recall on gold is not 100% by design)
- Exit: `python -m guiml_bench.cli grade-gold` exits 0

## Phase 4 — Conditions and GUIML
- [x] Providers: Mistral, OpenAI, Anthropic, HF Inference, mock
- [x] B0, B1, B2, B3
- [x] GUIML JSON Schema
- [x] Retrieval by rule class
- [x] Linter + `replaces` rewrite + repair ≤ 2
- [x] Compiler → `@carbon/react` TSX
- [x] Ablations T-lint, T-life, T+MoE
- Exit: smoke profile produces a cell per condition

## Phase 5 — Runner and dress rehearsal
- [x] Async runner, per-cell cache, profiles smoke/tier1/tier2/tier3/demo
- [x] Grade as cells land
- [x] `estimate` prints cells, USD, wall-clock
- [x] Smoke on mock
- [x] Demo dress rehearsal (224 cells) used as resume/cache proof: rerunning skips `grades.json`
- [x] `RUN.md`
- Exit: `python -m guiml_bench.cli run --profile smoke --models mock`

## Phase 6 — Run day (one day)
- [x] Harness ready; Tier 1 estimated at 4,800 cells / ~$168 / ~1.1h @30-way
- [x] Dress rehearsal executed (`runs/demo-mock`, 224 cells, mock provider) — **not a scientific result**
- [ ] Paid Tier 1/2/3 with frontier keys (see `RUN.md`; requires `MISTRAL_API_KEY` / `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` / `HF_TOKEN`)
- Fallback: Tier 1 alone answers RQ1, RQ3, RQ5

## Phase 7 — Analysis
- [ ] Human κ labelling (paper-time)
- [x] Stats pipeline: OLS/mixedlm, heatmap, scale curve, cost table (`guiml_bench.stats.write_report`)
- [x] Figures from demo-mock in `runs/demo-mock/figures` and `paper/figures`
- [ ] Findings from the paid matrix

## Phase 8 — Publish artifacts
- [x] Local staging in `dist/hf/` (tasks.jsonl, gold.jsonl, packs, GUIML graphs, dataset cards)
- [x] Gradio Space app in `space/`
- [x] `pip install -e .`; README + RUN.md with cost estimate
- [ ] `hf auth login` then `python -m guiml_bench.cli push-hf --repo blu-octopus/guiml-bench` (MCP is logged in as blu-octopus; the local `huggingface_hub` client has no token yet)

## Phase 9 — Paper
- [x] IEEEtran draft: `paper/main.tex`
- [x] CHI workshop position paper: `paper/chi-workshop.md`
- [ ] Advisor review
- [ ] Submit

---

## Dependencies

```
P1 extract ─► P2 tasks ─► P3 graders ─► P5 runner ─► P6 run ─► P7 analysis ─► P9 paper
      │                       ▲                                     │
      └──► P4 conditions/GUIML┘                                     └─► P8 artifacts
```

## Risks and responses
- Run-day API failures → per-cell retry, resume, tiered priority
- Judge disagreement on R3 → κ gating, report R3 separately
- GUIML does not beat B3 on R1/R2 → expected; claims are R3/R5 and scale
- Budget overrun → Tier 3 to 2 models; Tier 2 to 2 reps
- Carbon version drift → pinned commit, versioned packs, benchmark version tag
