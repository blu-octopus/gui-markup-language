from __future__ import annotations

import json
from pathlib import Path

from guiml_bench.paths import CARBON_OUT, DATA, GOLD_DIR, GUIML_DIR, ROOT, SPACE, TASKS_DIR
from guiml_bench.tasks.schema import load_tasks


def _dataset_card(name: str, body: str) -> str:
    return f"---\nlicense: mit\ntask_categories:\n- text-generation\nlanguage:\n- en\ntags:\n- design-systems\n- generative-ui\n- carbon\npretty_name: {name}\n---\n\n{body}\n"


def prepare_export(dest: Path) -> Path:
    dest.mkdir(parents=True, exist_ok=True)
    tasks = [t.model_dump() for t in load_tasks()]
    (dest / "tasks.jsonl").write_text("\n".join(json.dumps(t) for t in tasks), encoding="utf-8")
    (dest / "README_tasks.md").write_text(
        _dataset_card("GUIML-Bench tasks", "80 intent-level UI generation tasks tagged with R1–R6 checkpoints on IBM Carbon v11."),
        encoding="utf-8",
    )
    gold = []
    for p in sorted(GOLD_DIR.glob("*.tsx")):
        if p.name.startswith("_"):
            continue
        gold.append({"id": p.stem, "tsx": p.read_text(encoding="utf-8")})
    (dest / "gold.jsonl").write_text("\n".join(json.dumps(g) for g in gold), encoding="utf-8")
    for scale in "SML":
        src = GUIML_DIR / f"carbon-{scale.lower()}.guiml.json"
        if src.exists():
            (dest / src.name).write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
    for name in ("tokens.json", "components.json", "lifecycle.json", "pack-S.json", "pack-M.json", "pack-L.json"):
        src = CARBON_OUT / name
        if src.exists():
            (dest / name).write_bytes(src.read_bytes())
    (dest / "README_carbon.md").write_text(
        _dataset_card("GUIML-Bench Carbon rule graph", "IBM Carbon v11 tokens, components, lifecycle table, S/M/L packs, and GUIML system graphs."),
        encoding="utf-8",
    )
    return dest


def push(repo: str, private: bool = True) -> None:
    dest = prepare_export(ROOT / "dist" / "hf")
    from guiml_bench.paths import RUNS_DIR
    demo = RUNS_DIR / "demo-mock" / "results.json"
    if demo.exists():
        (dest / "results.json").write_bytes(demo.read_bytes())
    try:
        from huggingface_hub import HfApi
    except ImportError as e:
        print("staged at", dest, "(pip install 'guiml-bench[hf]' to upload)")
        return
    # create repos if possible
    ns = repo if "/" in repo else None
    print("export staged at", dest)
    print("To publish:")
    print(f"  huggingface-cli upload {repo}-tasks {dest}/tasks.jsonl --repo-type dataset")
    print(f"  huggingface-cli upload {repo}-carbon {dest}/carbon-l.guiml.json --repo-type dataset")
    print("Space files live in space/")
    try:
        api.whoami()
    except Exception:
        print("not logged in; ran a dry export only")
        return
    print("logged in; leaving upload to the user unless HF_TOKEN is used with huggingface-cli")
