"""Gradio leaderboard for GUIML-Bench runs."""
from __future__ import annotations

import json
from collections import defaultdict

import gradio as gr

CLASSES = ["R1", "R2", "R3", "R4", "R5", "R6"]


def summarize(results_json: str) -> tuple[list[list], str]:
    try:
        data = json.loads(results_json)
    except json.JSONDecodeError as e:
        return [], f"invalid JSON: {e}"
    agg = defaultdict(lambda: {"n": 0, "gs": 0.0, **{c: 0.0 for c in CLASSES}})
    for r in data:
        key = (r.get("condition"), r.get("scale"), r.get("model"))
        a = agg[key]
        a["n"] += 1
        a["gs"] += float(r.get("gs") or 0)
        per = r.get("per_class") or {}
        for c in CLASSES:
            a[c] += 1.0 if (per.get(c) or {}).get("pass") else 0.0
    rows = []
    for (cond, scale, model), a in sorted(agg.items()):
        n = max(a["n"], 1)
        rows.append([cond, scale, model, a["n"], round(a["gs"] / n, 3), *[round(a[c] / n, 3) for c in CLASSES]])
    header = "condition | scale | model | n | GS | " + " | ".join(CLASSES)
    return rows, f"{len(data)} samples. Columns: {header}"


with gr.Blocks(title="GUIML-Bench") as demo:
    gr.Markdown(
        "# GUIML-Bench leaderboard\n"
        "Paste a `results.json` produced by `guiml-bench run`. "
        "Scores are Governance Score and per-class pass rates (R1–R6)."
    )
    inp = gr.Textbox(lines=12, label="results.json")
    btn = gr.Button("Score")
    table = gr.Dataframe(
        headers=["condition", "scale", "model", "n", "GS", *CLASSES],
        label="Aggregates",
    )
    note = gr.Markdown()
    btn.click(summarize, inp, [table, note])

if __name__ == "__main__":
    demo.launch()
