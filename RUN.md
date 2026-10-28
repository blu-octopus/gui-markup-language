# Running GUIML-Bench

## One-time extract

```bash
cd carbon && npm install && npm run extract && cd ..
python -m guiml_bench.cli extract
python -m guiml_bench.cli validate-tasks
python -m guiml_bench.cli grade-gold
```

## Smoke (no API keys)

```bash
python -m guiml_bench.cli run --profile smoke --models mock
python -m guiml_bench.cli report --run <run-id>
```

The `demo` profile runs 8 tasks × 7 conditions × {S,L} × 2 reps on the mock provider and is what CI uses to keep the stats pipeline honest.

## Paid run day

Export keys, then estimate, then run tiers in order. Resume is implicit: cells with `grades.json` are skipped.

```bash
export MISTRAL_API_KEY=...
export OPENAI_API_KEY=...
export ANTHROPIC_API_KEY=...
export HF_TOKEN=...

python -m guiml_bench.cli estimate --profile tier1
python -m guiml_bench.cli run --profile tier1 --concurrency 20 --run-id day-tier1
python -m guiml_bench.cli run --profile tier2 --concurrency 20 --run-id day-tier2
python -m guiml_bench.cli run --profile tier3 --concurrency 20 --run-id day-tier3
python -m guiml_bench.cli report --run day-tier1
```

If a provider is missing, pass `--models mistral:mistral-large-latest` (or whatever you have) to shrink the matrix. Tier 1 alone answers RQ1, RQ3, RQ5.

## Hugging Face

```bash
python -m guiml_bench.cli push-hf --repo YOUR_HF_USER/guiml-bench
# then copy space/ to a Gradio Space
```
