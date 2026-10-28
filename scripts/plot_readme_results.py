#!/usr/bin/env python3
"""Build the public README figures from the Carbon extract and a bench run.

The mock dress-rehearsal numbers are a harness check, not a model result.
Regenerate after a paid run with:

    python scripts/plot_readme_results.py --run <run-id>
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs" / "assets"
RESULTS = ROOT / "docs" / "results"
PAPER_FIGS = ROOT / "paper" / "figures"

CONDS = ["B0", "B1", "B2", "B3", "T", "T-lint", "T-life"]
CLASSES = ["R1", "R2", "R3", "R4", "R5", "R6"]
COND_COLORS = {
    "B0": "#8d8d8d",
    "B1": "#ff832b",
    "B2": "#24a148",
    "B3": "#8a3ffc",
    "T": "#0f62fe",
    "T-lint": "#1192e8",
    "T-life": "#007d79",
}


def _style() -> None:
    plt.rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": ["IBM Plex Sans", "Helvetica Neue", "Arial", "DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.titleweight": "medium",
            "axes.labelsize": 10,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.edgecolor": "#525252",
            "axes.labelcolor": "#161616",
            "text.color": "#161616",
            "xtick.color": "#161616",
            "ytick.color": "#161616",
            "figure.facecolor": "white",
            "axes.facecolor": "white",
            "savefig.facecolor": "white",
            "savefig.bbox": "tight",
            "savefig.dpi": 160,
        }
    )


def carbon_extract() -> dict:
    packs = json.loads((ROOT / "carbon" / "out" / "packs.json").read_text())
    life = json.loads((ROOT / "carbon" / "out" / "lifecycle.json").read_text())
    graphs = {}
    for scale in "SML":
        g = json.loads((ROOT / "guiml" / f"carbon-{scale.lower()}.guiml.json").read_text())
        graphs[scale] = {
            "nodes": len(g["nodes"]),
            "edges": len(g["edges"]),
            "nodes_by_kind": dict(Counter(n["kind"] for n in g["nodes"])),
            "edges_by_kind": dict(Counter(e["kind"] for e in g["edges"])),
        }
    tasks = list((ROOT / "data" / "tasks").glob("*.yaml"))
    gold = [p for p in (ROOT / "data" / "gold").glob("*.tsx") if not p.name.startswith("_")]
    return {
        "packs": packs["packs"],
        "lifecycle": life.get("counts", {}),
        "graphs": graphs,
        "tasks": len(tasks),
        "gold": len(gold),
        "source": {
            "themes": "@carbon/themes 11.84",
            "react": "@carbon/react 1.119",
        },
    }


def load_run_tables(run: str | None) -> tuple[pd.DataFrame, pd.DataFrame]:
    run_dir = ROOT / "runs" / run if run else None
    summary_path = (run_dir / "figures" / "summary.csv") if run_dir else None
    cost_path = (run_dir / "figures" / "cost_latency.csv") if run_dir else None
    if not (summary_path and summary_path.exists()):
        summary_path = RESULTS / "summary.csv"
        cost_path = RESULTS / "cost_latency.csv"
    summary = pd.read_csv(summary_path)
    cost = pd.read_csv(cost_path)
    return summary, cost


def _save(fig: plt.Figure, name: str) -> None:
    ASSETS.mkdir(parents=True, exist_ok=True)
    PAPER_FIGS.mkdir(parents=True, exist_ok=True)
    for dest in (ASSETS / name, PAPER_FIGS / name):
        fig.savefig(dest)
    plt.close(fig)


def plot_pack_sizes(extract: dict) -> None:
    packs = extract["packs"]
    scales = ["S", "M", "L"]
    tokens = [packs[s]["tokens"] for s in scales]
    comps = [packs[s]["components"] for s in scales]
    x = np.arange(len(scales))
    w = 0.36
    fig, ax = plt.subplots(figsize=(5.6, 3.6))
    ax.bar(x - w / 2, tokens, w, label="tokens", color="#0f62fe")
    ax.bar(x + w / 2, comps, w, label="components", color="#8a3ffc")
    for i, (t, c) in enumerate(zip(tokens, comps)):
        ax.text(i - w / 2, t + 6, str(t), ha="center", va="bottom", fontsize=9)
        ax.text(i + w / 2, c + 6, str(c), ha="center", va="bottom", fontsize=9)
    ax.set_xticks(x, scales)
    ax.set_ylabel("Count")
    ax.set_title("Carbon v11 packs (L contains M contains S)")
    ax.set_ylim(0, max(tokens) * 1.18)
    ax.legend(frameon=False)
    fig.tight_layout()
    _save(fig, "pack_sizes.png")


def plot_gs_bars(summary: pd.DataFrame) -> None:
    gs = summary.groupby("condition")["gs"].mean().reindex(CONDS)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    colors = [COND_COLORS[c] for c in gs.index]
    bars = ax.bar(gs.index, gs.values, color=colors, width=0.72)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Governance Score")
    ax.set_title("Governance Score by condition (mock dress rehearsal)")
    for bar, val in zip(bars, gs.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.02, f"{val:.2f}", ha="center", va="bottom", fontsize=9)
    fig.tight_layout()
    _save(fig, "gs_by_condition.png")


def plot_heatmap(summary: pd.DataFrame) -> None:
    heat = summary.groupby("condition")[CLASSES].mean().reindex(CONDS)
    data = heat.to_numpy()
    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    cmap = plt.cm.colors.LinearSegmentedColormap.from_list("ibm", ["#161616", "#4589ff", "#a6c8ff"])
    im = ax.imshow(data, aspect="auto", vmin=0, vmax=1, cmap=cmap)
    ax.set_xticks(range(len(CLASSES)), CLASSES)
    ax.set_yticks(range(len(heat.index)), list(heat.index))
    ax.set_title("Pass rate by condition × rule class")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            ax.text(j, i, f"{val:.2f}", ha="center", va="center", color="white" if val < 0.55 else "#161616", fontsize=9)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()
    _save(fig, "heatmap_class_condition.png")


def plot_tokens(cost: pd.DataFrame) -> None:
    col = "condition" if "condition" in cost.columns else cost.columns[0]
    if col != "condition":
        cost = cost.rename(columns={col: "condition"})
    series = cost.set_index("condition")["tokens_in"].reindex(CONDS)
    fig, ax = plt.subplots(figsize=(6.4, 3.6))
    colors = [COND_COLORS[c] for c in series.index]
    bars = ax.bar(series.index, series.values, color=colors, width=0.72)
    ax.set_ylabel("Mean prompt tokens")
    ax.set_title("Context budget by condition")
    for bar, val in zip(bars, series.values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val + max(series.values) * 0.02,
            f"{val:,.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
    ax.set_ylim(0, max(series.values) * 1.18)
    fig.tight_layout()
    _save(fig, "context_budget.png")


def plot_hero(summary: pd.DataFrame, cost: pd.DataFrame, extract: dict) -> None:
    gs = summary.groupby("condition")["gs"].mean().reindex(CONDS)
    heat = summary.groupby("condition")[CLASSES].mean().reindex(CONDS)
    cost = cost.copy()
    col = "condition" if "condition" in cost.columns else cost.columns[0]
    if col != "condition":
        cost = cost.rename(columns={col: "condition"})
    tokens = cost.set_index("condition")["tokens_in"].reindex(CONDS)
    packs = extract["packs"]

    fig, axes = plt.subplots(2, 2, figsize=(11.2, 7.6))
    fig.suptitle("GUIML-Bench · mock dress rehearsal (224 cells)", fontsize=13, fontweight="medium", y=0.98)

    ax = axes[0, 0]
    colors = [COND_COLORS[c] for c in gs.index]
    bars = ax.bar(gs.index, gs.values, color=colors, width=0.72)
    ax.set_ylim(0, 1.12)
    ax.set_ylabel("Governance Score")
    ax.set_title("(a) Governance Score")
    for bar, val in zip(bars, gs.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + 0.03, f"{val:.2f}", ha="center", va="bottom", fontsize=8)

    ax = axes[0, 1]
    data = heat.to_numpy()
    cmap = plt.cm.colors.LinearSegmentedColormap.from_list("ibm", ["#161616", "#4589ff", "#a6c8ff"])
    im = ax.imshow(data, aspect="auto", vmin=0, vmax=1, cmap=cmap)
    ax.set_xticks(range(len(CLASSES)), CLASSES)
    ax.set_yticks(range(len(heat.index)), list(heat.index))
    ax.set_title("(b) Pass rate by rule class")
    for i in range(data.shape[0]):
        for j in range(data.shape[1]):
            val = data[i, j]
            ax.text(j, i, f"{val:.1f}", ha="center", va="center", color="white" if val < 0.55 else "#161616", fontsize=8)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.03)

    ax = axes[1, 0]
    colors = [COND_COLORS[c] for c in tokens.index]
    bars = ax.bar(tokens.index, tokens.values, color=colors, width=0.72)
    ax.set_ylabel("Mean prompt tokens")
    ax.set_title("(c) Context budget")
    ymax = max(tokens.values)
    ax.set_ylim(0, ymax * 1.22)
    for bar, val in zip(bars, tokens.values):
        ax.text(bar.get_x() + bar.get_width() / 2, val + ymax * 0.03, f"{val:,.0f}", ha="center", va="bottom", fontsize=8)

    ax = axes[1, 1]
    scales = ["S", "M", "L"]
    tok = [packs[s]["tokens"] for s in scales]
    comp = [packs[s]["components"] for s in scales]
    x = np.arange(len(scales))
    w = 0.36
    ax.bar(x - w / 2, tok, w, label="tokens", color="#0f62fe")
    ax.bar(x + w / 2, comp, w, label="components", color="#8a3ffc")
    for i, (t, c) in enumerate(zip(tok, comp)):
        ax.text(i - w / 2, t + 8, str(t), ha="center", va="bottom", fontsize=8)
        ax.text(i + w / 2, c + 8, str(c), ha="center", va="bottom", fontsize=8)
    ax.set_xticks(x, scales)
    ax.set_ylabel("Count")
    ax.set_title("(d) Carbon v11 pack size")
    ax.set_ylim(0, max(tok) * 1.2)
    ax.legend(frameon=False, loc="upper left")

    fig.tight_layout(rect=(0, 0, 1, 0.96))
    _save(fig, "pilot-results.png")


def write_summary_json(extract: dict, summary: pd.DataFrame, cost: pd.DataFrame) -> None:
    RESULTS.mkdir(parents=True, exist_ok=True)
    gs = summary.groupby("condition")["gs"].mean().reindex(CONDS)
    heat = summary.groupby("condition")[CLASSES].mean().reindex(CONDS)
    cost = cost.copy()
    col = "condition" if "condition" in cost.columns else cost.columns[0]
    if col != "condition":
        cost = cost.rename(columns={col: "condition"})
    cost_idx = cost.set_index("condition")
    payload = {
        "note": "Mock-provider dress rehearsal. Not a scientific finding. Paid matrix is in RUN.md.",
        "profile": "demo",
        "provider": "mock",
        "cells": 224,
        "tasks": 8,
        "conditions": CONDS,
        "scales": ["S", "L"],
        "reps": 2,
        "governance_score": {k: round(float(v), 4) for k, v in gs.items()},
        "pass_rate": {cond: {c: round(float(heat.loc[cond, c]), 4) for c in CLASSES} for cond in CONDS},
        "mean_prompt_tokens": {k: round(float(cost_idx.loc[k, "tokens_in"]), 1) for k in CONDS},
        "carbon": extract,
    }
    (RESULTS / "demo-mock-summary.json").write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    summary.to_csv(RESULTS / "summary.csv", index=False)
    cost.to_csv(RESULTS / "cost_latency.csv", index=False)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--run", default="demo-mock", help="run id under runs/, or omit to use docs/results")
    args = p.parse_args()
    _style()
    extract = carbon_extract()
    summary, cost = load_run_tables(args.run)
    plot_pack_sizes(extract)
    plot_gs_bars(summary)
    plot_heatmap(summary)
    plot_tokens(cost)
    plot_hero(summary, cost, extract)
    write_summary_json(extract, summary, cost)
    print("wrote", ASSETS)
    print("wrote", RESULTS / "demo-mock-summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
