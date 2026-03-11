import itertools
import json
from pathlib import Path
from pprint import pp

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from fontTools.t1Lib import ND_values

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


df = build_df_from_all_eval_json_files(all_eval_json_paths)
df.to_csv(DIR_DATA / "all_eval_data.csv", index=False)


print(f"Total samples: {df.shape[0]}")

df_pass = df[
    [
        "eval_id",
        "eval_index",
        "benchmark_case_name",
        "benchmark_case_tags",
        "model_name",
        "pass_parse",
        "pass_compile",
        "pass_tb",
        "pass_synth",
    ]
]
df_pass["pass_tb_and_synth"] = df_pass["pass_tb"] & df_pass["pass_synth"]


def compute_pass_rates_custom(df: pd.DataFrame, ks=[1, 5]):
    _models = df["model_name"].unique()
    _eval_ids = df["eval_id"].unique()

    data_pass_at_k = []

    for eval_id, df_group in df.groupby("eval_id"):
        # print(f"Eval ID: {eval_id}")
        # print(df_group)
        n_samples = df_group.shape[0]
        n_pass_parse = df_group["pass_parse"].sum()
        n_pass_compile = df_group["pass_compile"].sum()
        n_pass_tb = df_group["pass_tb"].sum()
        n_pass_synth = df_group["pass_synth"].sum()
        n_pass_tb_and_synth = df_group["pass_tb_and_synth"].sum()

        for k in ks:
            pass_at_k_parse = pass_at_k(n_samples, n_pass_parse, k)
            pass_at_k_compile = pass_at_k(n_samples, n_pass_compile, k)
            pass_at_k_tb = pass_at_k(n_samples, n_pass_tb, k)
            pass_at_k_synth = pass_at_k(n_samples, n_pass_synth, k)
            pass_at_k_tb_and_synth = pass_at_k(n_samples, n_pass_tb_and_synth, k)

            pass_at_k_vals = {
                "pass_parse": pass_at_k_parse,
                "pass_compile": pass_at_k_compile,
                "pass_tb": pass_at_k_tb,
                "pass_synth": pass_at_k_synth,
                "pass_tb_and_synth": pass_at_k_tb_and_synth,
            }

            for pass_at_k_key in pass_at_k_vals:
                data_pass_at_k.append(
                    {
                        "eval_id": eval_id,
                        "model_name": df_group["model_name"].iloc[0],
                        "benchmark_case_name": df_group["benchmark_case_name"].iloc[0],
                        "benchmark_case_tags": df_group["benchmark_case_tags"].iloc[0],
                        "metric_name": pass_at_k_key,
                        "k": k,
                        "pass_rate": pass_at_k_vals[pass_at_k_key],
                    }
                )
    # pprint(data_pass_at_k)
    df_new = pd.DataFrame(
        data_pass_at_k,
        columns=[
            "eval_id",
            "model_name",
            "benchmark_case_name",
            "benchmark_case_tags",
            "metric_name",
            "k",
            "pass_rate",
        ],
    )
    # now what we want to do is for each (metric, k) we want to compute the avcge for each model over all evals
    # df_agg = (
    #     df_new.groupby(["model_name", "metric_name", "k"])
    #     .agg({"pass_rate": "mean"})
    #     .reset_index()
    # )
    # show all the columns
    pd.set_option("display.max_columns", None)
    print(df_new.head())

    # turn the tags colum from list to set
    df_new["benchmark_case_tags"] = df_new["benchmark_case_tags"].apply(
        lambda x: set(x) if isinstance(x, list) else set()
    )
    # if there is one item in the set, then we can just use that as the tag, otherwise we can use "multiple"
    df_new["benchmark_case_tags"] = df_new["benchmark_case_tags"].apply(
        lambda x: list(x)[0] if len(x) == 1 else "multiple"
    )

    # group by stuff other than model name and compute the mean, then we can plot with seaborn
    df_agg = (
        df_new.groupby(
            [
                "model_name",
                "benchmark_case_tags",
                "metric_name",
                "k",
            ]
        )
        .agg({"pass_rate": "mean"})
        .reset_index()
    )

    # also agg by benchamrk case name, and then we can see if there are any cases that are particularly hard or easy
    df_agg_case = (
        df_new.groupby(
            [
                "model_name",
                "benchmark_case_name",
                "metric_name",
                "k",
            ]
        )
        .agg({"pass_rate": "mean"})
        .reset_index()
    )

    return df_agg, df_agg_case


pass_rate_byt_tag, pass_rate_by_case = compute_pass_rates_custom(df_pass, ks=[1, 5, 10])

pass_rate_byt_tag.sort_values(
    by=["benchmark_case_tags", "model_name", "metric_name", "k"],
    inplace=True,
)
pass_rate_byt_tag.to_csv(DIR_DATA / "pass_rates_by_tag.csv", index=False)

pass_rate_by_case.sort_values(
    by=["benchmark_case_name", "model_name", "metric_name", "k"],
    inplace=True,
)
pass_rate_by_case.to_csv(DIR_DATA / "pass_rates_by_case.csv", index=False)

print(pass_rate_byt_tag.head())

# make a pas rate plot, but insted of one line per model, we have one line per tag, and we pick one mdoel

df_pass_rate_byt_tag_oss_gpt_120b = pass_rate_byt_tag[
    pass_rate_byt_tag["model_name"] == "openai/gpt-oss-120b"
]


def plot_pass_rates_line_modified(
    df_pass_rates, title: str, ks=[1, 5], leg_ncols: int = 2
):
    # models = df_pass_rates["model_name"].unique()
    tags = df_pass_rates["benchmark_case_tags"].unique()
    # n_models = len(models)
    n_tags = len(tags)

    colors = matplotlib.cm.tab20(range(20))
    cm = plt.get_cmap("tab20")
    tags_to_color = {tag: cm(i) for i, tag in enumerate(tags)}

    # model_to_color = {model: model_color_map[model] for model in models}
    # tags_to_color = {tag: model_color_map[tag] for tag in tags}

    fig, ax = plt.subplots(1, 1, figsize=(6, 3.5))

    ax.grid(axis="y", linestyle="--", alpha=0.8, zorder=-10)
    ax.set_axisbelow(True)

    coord_to_stage = {
        0: "pass_parse",
        1: "pass_compile",
        2: "pass_tb",
        3: "pass_synth",
    }

    # models = df_pass_rates["model_name"].unique()
    tags = df_pass_rates["benchmark_case_tags"].unique()
    combos = list(itertools.product(tags, ks))

    for tag, k in combos:
        print(f"Processing tag: {tag}, k: {k}")
        df_filtered = df_pass_rates[
            (df_pass_rates["benchmark_case_tags"] == tag) & (df_pass_rates["k"] == k)
        ]
        pass_parse = df_filtered[df_filtered["metric_name"] == "pass_parse"][
            "pass_rate"
        ]
        pass_compile = df_filtered[df_filtered["metric_name"] == "pass_compile"][
            "pass_rate"
        ]
        pass_tb = df_filtered[df_filtered["metric_name"] == "pass_tb"]["pass_rate"]
        pass_synth = df_filtered[df_filtered["metric_name"] == "pass_synth"][
            "pass_rate"
        ]
        color = tags_to_color[tag]
        if k == 1:
            linestyle = "--"
        else:
            linestyle = "-"
        ax.plot(
            np.arange(0, 4),
            [pass_parse, pass_compile, pass_tb, pass_synth],
            marker="o",
            markersize=4,
            color=color,
            linestyle=linestyle,
            label=f"{tag} - pass@{k}",
        )

    ax.axhline(y=1, color="black", linestyle="--", alpha=1.0, zorder=1, linewidth=1)

    # add virtiline dashed gray lines at each stage
    for i in range(4):
        ax.axvline(
            x=i, color="gray", linestyle="--", alpha=0.5, zorder=-10, linewidth=1
        )

    ax.set_xticks(np.arange(0, 4))
    ax.set_xticklabels(
        [
            metric_name_map[metric]
            for metric in ["pass_parse", "pass_compile", "pass_tb", "pass_synth"]
        ],
        rotation=0,
        ha="center",
    )
    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_yticklabels(
        [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
    )  # format as percent in 10% increments

    ax.set_ylim(0, 1.05)

    ax.set_ylabel("Pass Rate")

    ax.legend(loc="lower left", ncol=leg_ncols, fontsize=7.5, handlelength=3)

    # ax.set_title(label="Pass Rate of Zero-Shot Editing by Model: Loop Tiling")
    ax.set_title(title)

    fig.tight_layout()
    return fig


fig = plot_pass_rates_line_modified(
    df_pass_rate_byt_tag_oss_gpt_120b,
    title="Pass Rates by Benchmark Case Tag for openai/gpt-oss-120b",
    ks=[1, 10],
)
fig.savefig(DIR_FIGURES / "pass_rates_by_tag_oss_gpt_120b.png", dpi=300)
