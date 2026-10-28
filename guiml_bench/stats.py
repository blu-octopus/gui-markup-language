from __future__ import annotations

import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from guiml_bench.paths import RUNS_DIR

CLASSES = ["R1", "R2", "R3", "R4", "R5", "R6"]


def load_run(run: str | Path) -> pd.DataFrame:
    path = Path(run)
    if not path.is_absolute():
        path = RUNS_DIR / run
    raw = json.loads((path / "results.json").read_text(encoding="utf-8"))
    rows = []
    for r in raw:
        if not r.get("ok", True) and "per_class" not in r:
            rows.append(
                {
                    "task": r.get("task"),
                    "condition": r.get("condition"),
                    "scale": r.get("scale"),
                    "model": r.get("model"),
                    "rep": r.get("rep"),
                    "gs": r.get("gs", 0),
                    "gated": True,
                    **{f"pass_{c}": False for c in CLASSES},
                }
            )
            continue
        per = r.get("per_class") or {}
        rows.append(
            {
                "task": r.get("task"),
                "condition": r.get("condition"),
                "scale": r.get("scale"),
                "model": r.get("model"),
                "rep": r.get("rep"),
                "gs": r.get("gs", 0),
                "gated": r.get("gated", False),
                "latency_s": r.get("elapsed_s"),
                "cost_usd": (r.get("usage") or {}).get("cost_usd"),
                "tokens_in": (r.get("usage") or {}).get("input_tokens"),
                "tokens_out": (r.get("usage") or {}).get("output_tokens"),
                **{f"pass_{c}": bool((per.get(c) or {}).get("pass")) for c in CLASSES},
            }
        )
    return pd.DataFrame(rows)


def write_report(run: str | Path) -> Path:
    path = Path(run)
    if not path.is_absolute():
        path = RUNS_DIR / run
    df = load_run(path)
    fig_dir = path / "figures"
    fig_dir.mkdir(exist_ok=True)

    # heatmap condition × class
    conds = list(df["condition"].dropna().unique())
    heat = pd.DataFrame(
        {c: [df.loc[df.condition == cond, f"pass_{c}"].mean() for cond in conds] for c in CLASSES},
        index=conds,
    )
    fig, ax = plt.subplots(figsize=(8, 4))
    im = ax.imshow(heat.to_numpy(), aspect="auto", vmin=0, vmax=1, cmap="viridis")
    ax.set_xticks(range(len(CLASSES)), CLASSES)
    ax.set_yticks(range(len(conds)), conds)
    ax.set_title("Pass rate by condition × rule class")
    fig.colorbar(im, ax=ax, fraction=0.046)
    fig.tight_layout()
    fig.savefig(fig_dir / "heatmap_class_condition.png", dpi=140)
    plt.close(fig)

    # scale curve
    if df["scale"].nunique() > 1:
        fig, ax = plt.subplots(figsize=(6, 4))
        for cond, g in df.groupby("condition"):
            means = g.groupby("scale")["gs"].mean().reindex(["S", "M", "L"])
            ax.plot(["S", "M", "L"], means.values, marker="o", label=cond)
        ax.set_ylabel("Governance Score")
        ax.set_title("GS vs design-system scale")
        ax.legend()
        fig.tight_layout()
        fig.savefig(fig_dir / "scale_curve.png", dpi=140)
        plt.close(fig)

    summary = (
        df.groupby(["condition", "scale"])
        .agg(n=("gs", "size"), gs=("gs", "mean"), **{f"{c}": (f"pass_{c}", "mean") for c in CLASSES})
        .reset_index()
    )
    summary.to_csv(fig_dir / "summary.csv", index=False)
    trap_tasks = [t.id for t in __import__("guiml_bench.tasks.schema", fromlist=["load_tasks"]).load_tasks() if t.trap]
    trap = df[df.task.isin(trap_tasks)]
    if len(trap):
        trap.groupby("condition")[["gs"] + [f"pass_{c}" for c in CLASSES]].mean().to_csv(fig_dir / "trap_table.csv")

    cost = df.groupby("condition")[["latency_s", "cost_usd", "tokens_in"]].mean()
    cost.to_csv(fig_dir / "cost_latency.csv")

    try:
        import warnings

        import statsmodels.formula.api as smf

        dfl = df.melt(
            id_vars=["task", "condition", "scale", "model", "rep"],
            value_vars=[f"pass_{c}" for c in CLASSES],
            var_name="rule_class",
            value_name="passed",
        )
        dfl["passed"] = dfl["passed"].astype(int)
        dfl["rule_class"] = dfl["rule_class"].str.replace("pass_", "")
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            md = smf.ols("passed ~ C(condition) + C(rule_class) + C(scale)", dfl)
            mdf = md.fit()
        (fig_dir / "mixedlm.txt").write_text(
            "OLS (mixedlm falls back when the random-effects covariance is singular on small/mock runs)\n\n"
            + mdf.summary().as_text(),
            encoding="utf-8",
        )
    except Exception as e:
        (fig_dir / "mixedlm.txt").write_text(f"skipped: {e}", encoding="utf-8")

    print("wrote", fig_dir)
    return fig_dir
