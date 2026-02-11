import itertools
import json
from pathlib import Path
from pprint import pp

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns

from hls_eval_experiments.exp_utils import (
    build_df_from_all_eval_json_files,
    build_pass_table,
    compute_pass_rates,
    metric_name_map,
    model_color_map,
    model_name_map,
    pass_at_k,
    plot_pass_rates_bar,
    plot_pass_rates_line,
)

DIR_CURRENT = Path(__file__).resolve().parent
DIR_INPUT_DATA = DIR_CURRENT / "output_data_v1"

DIR_FIGURES = DIR_CURRENT / "figures"
if not DIR_FIGURES.exists():
    DIR_FIGURES.mkdir()
DIR_DATA = DIR_CURRENT / "data"
if not DIR_DATA.exists():
    DIR_DATA.mkdir()

# count how many are missing the single_eval_data.json
missing = []
for eval_case_run_dir in DIR_INPUT_DATA.iterdir():
    eval_data_fp = eval_case_run_dir / "all_eval_data.json"
    if not eval_data_fp.exists():
        missing.append(eval_case_run_dir.name)

if len(missing) > 0:
    print(missing)
    raise ValueError(f"Missing data from {len(missing)} evals")

all_eval_json_paths = []
for eval_case_run_dir in DIR_INPUT_DATA.iterdir():
    eval_data_fp = eval_case_run_dir / "all_eval_data.json"
    all_eval_json_paths.append(eval_data_fp)


# ─────────────────────────────────────────────
# Build trace-level dataframe
# ─────────────────────────────────────────────


def build_trace_df(all_eval_json_paths: list[Path]) -> pd.DataFrame:
    """Parse agent traces and extract per-sample token / step metrics."""
    rows = []
    for fp in all_eval_json_paths:
        data = json.loads(fp.read_text())
        for eval_index, ev in data.items():
            pass_tb = False
            if "c_run_out" in ev:
                pass_tb = ev["c_run_out"]["data_execution"]["return_code"] == 0

            pass_synth = False
            if "vitis_hls_tool_out" in ev:
                pass_synth = (
                    ev["vitis_hls_tool_out"]["data_execution"]["return_code"] == 0
                )

            trace = ev.get("agent_trace", [])

            # Count assistant steps (LLM calls)
            n_steps = sum(1 for msg in trace if msg["role"] == "assistant")

            # Sum tokens across all assistant messages that carry usage info
            total_prompt_tokens = 0
            total_completion_tokens = 0
            total_tokens = 0
            for msg in trace:
                if msg["role"] != "assistant":
                    continue
                usage = msg.get("extra", {}).get("response", {}).get("usage", {})
                total_prompt_tokens += usage.get("prompt_tokens", 0)
                total_completion_tokens += usage.get("completion_tokens", 0)
                total_tokens += usage.get("total_tokens", 0)

            rows.append(
                {
                    "eval_id": ev["eval_id"],
                    "benchmark_case_name": ev["benchmark_case_name"],
                    "model_name": ev["model_name"],
                    "eval_index": int(eval_index),
                    "pass_tb": pass_tb,
                    "pass_synth": pass_synth,
                    "n_steps": n_steps,
                    "total_prompt_tokens": total_prompt_tokens,
                    "total_completion_tokens": total_completion_tokens,
                    "total_tokens": total_tokens,
                    "agent_submitted": ev.get("agent_submitted", False),
                    "agent_limit_exceeded": ev.get("agent_limit_exceeded", False),
                }
            )
    return pd.DataFrame(rows)


df_traces = build_trace_df(all_eval_json_paths)
print(
    f"Loaded {len(df_traces)} trace rows across {df_traces['model_name'].nunique()} models"
)
print(df_traces[["model_name", "pass_tb", "n_steps", "total_tokens"]].describe())


# ─────────────────────────────────────────────
# KDE plots: total tokens & steps by pass/fail
# ─────────────────────────────────────────────
# sns.set_theme(style="whitegrid")


def plot_kde_by_pass(
    df: pd.DataFrame,
    metric: str,
    pass_col: str,
    xlabel: str,
    title: str,
    out_path: Path,
    log_scale: bool = False,
    min_x: float | None = None,
):
    """KDE + rug plot of `metric` split by `pass_col`, one facet per model."""
    models = sorted(df["model_name"].unique())
    n_models = len(models)
    fig, axes = plt.subplots(1, n_models, figsize=(5 * n_models, 4), sharey=False)
    if n_models == 1:
        axes = [axes]

    pass_colors = {True: "#2ecc71", False: "#e74c3c"}
    pass_label_map = {
        "pass_tb": {True: "Pass TB", False: "Fail TB"},
        "pass_synth": {True: "Pass Synth", False: "Fail Synth"},
    }
    pass_labels = pass_label_map.get(pass_col, {True: "Pass", False: "Fail"})

    for ax, model in zip(axes, models):
        ax.grid(which="both", axis="both", linestyle="--", alpha=0.5)
        ax.set_axisbelow(True)
        df_m = df[df["model_name"] == model]
        for passed, grp in df_m.groupby(pass_col):
            vals = grp[metric].dropna()
            # if log_scale:
            #     vals = vals[vals > 0]
            # if len(vals) < 2:
            #     continue
            color = pass_colors[passed]
            label = f"{pass_labels[passed]} (n={len(vals)})"
            # plot_vals = np.log10(vals) if log_scale else vals
            plot_vals = vals

            # if clip is not none and log is true, then the clip calue is log10(min_x)
            # else if log is not true, then the clip value is just min_x
            if log_scale and min_x is not None:
                clip_kwarg = np.log10(min_x)
            else:
                clip_kwarg = min_x

            sns.kdeplot(
                plot_vals,
                ax=ax,
                fill=True,
                alpha=0.35,
                color=color,
                label=label,
                log_scale=log_scale,
                clip=(clip_kwarg, None),
            )

        if metric == "n_steps":
            ax.set_xlim(left=1)

        display_name = model_name_map.get(model, model)
        ax.set_title(f"Model: {display_name}", fontsize=10)
        ax.set_xlabel(f"{xlabel}" if log_scale else xlabel)
        ax.set_ylabel("Density")
        ax.legend(fontsize=8)

    fig.suptitle(title, fontsize=12, y=1.02)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


def plot_kde_combined(
    df: pd.DataFrame,
    pass_col: str,
    title: str,
    out_path: Path,
):
    """2-row × N-model grid: row 0 = total tokens (log), row 1 = n_steps (log)."""
    model_order = ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]
    models = [m for m in model_order if m in df["model_name"].unique()]
    # fall back to sorted for any models not in the explicit order
    models += sorted(m for m in df["model_name"].unique() if m not in model_order)
    n_models = len(models)

    row_specs = [
        dict(metric="total_tokens", xlabel="Total tokens", log_scale=True, min_x=1),
        dict(metric="n_steps", xlabel="Number of agent steps", log_scale=True, min_x=1),
    ]

    pass_colors = {True: "#2ecc71", False: "#e74c3c"}
    pass_label_map = {
        "pass_tb": {True: "Pass TB", False: "Fail TB"},
        "pass_synth": {True: "Pass Synth", False: "Fail Synth"},
    }
    pass_labels = pass_label_map.get(pass_col, {True: "Pass", False: "Fail"})

    fig, axes = plt.subplots(
        2,
        n_models,
        figsize=(5 * n_models, 5),
        sharey=False,
    )
    # ensure axes is always 2-D
    if n_models == 1:
        axes = axes.reshape(2, 1)

    for row, spec in enumerate(row_specs):
        metric = spec["metric"]
        xlabel = spec["xlabel"]
        log_scale = spec["log_scale"]
        min_x = spec["min_x"]

        for col, model in enumerate(models):
            ax = axes[row, col]
            ax.grid(which="both", axis="both", linestyle="--", alpha=0.5)
            ax.set_axisbelow(True)

            df_m = df[df["model_name"] == model]
            for passed, grp in df_m.groupby(pass_col):
                vals = grp[metric].dropna()
                color = pass_colors[passed]
                label = f"{pass_labels[passed]} (n={len(vals)})"

                clip_kwarg = (
                    np.log10(min_x) if (log_scale and min_x is not None) else min_x
                )

                sns.kdeplot(
                    vals,
                    ax=ax,
                    fill=True,
                    alpha=0.35,
                    color=color,
                    label=label,
                    log_scale=log_scale,
                    clip=(clip_kwarg, None),
                )

            ax.set_xlabel(xlabel)
            ax.set_ylabel("Density")
            ax.legend(fontsize=8)
            if metric == "n_steps":
                ax.set_xlim(left=1)

            # column titles only on top row
            if row == 0:
                display_name = model_name_map.get(model, model)
                ax.set_title(f"Model: {display_name}", fontsize=10)

    fig.suptitle(title, fontsize=13, y=0.98)
    fig.tight_layout()
    fig.savefig(out_path, bbox_inches="tight", dpi=150)
    plt.close(fig)
    print(f"Saved: {out_path}")


plot_kde_combined(
    df_traces,
    pass_col="pass_tb",
    title="Agent Trace Distributions — Grouped by Pass vs Fail Testbench",
    out_path=DIR_FIGURES / "kde_combined_by_pass_tb.png",
)

plot_kde_combined(
    df_traces,
    pass_col="pass_synth",
    title="Agent Trace Distributions — Grouped by Pass vs Fail Synthesis",
    out_path=DIR_FIGURES / "kde_combined_by_pass_synth.png",
)


# ─────────────────────────────────────────────
# Summary stats table
# ─────────────────────────────────────────────

for pass_col, label in [("pass_tb", "pass_tb"), ("pass_synth", "pass_synth")]:
    summary = (
        df_traces.groupby(["model_name", pass_col])[["total_tokens", "n_steps"]]
        .agg(["mean", "median", "std", "count"])
        .round(1)
    )
    summary.index = summary.index.set_levels(
        [model_name_map.get(m, m) for m in summary.index.get_level_values(0).unique()],
        level=0,
    )
    out_csv = DIR_DATA / f"trace_summary_by_{label}.csv"
    print(f"\n=== Summary: tokens & steps by model and {label} ===")
    print(summary.to_string())
    summary.to_csv(out_csv)
    print(f"Saved: {out_csv}")
