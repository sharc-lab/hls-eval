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


df_pass_rates = compute_pass_rates(df_pass, ks=[1, 5, 10, 20])
df_pass_rates.to_csv(DIR_DATA / "pass_rates.csv", index=False)


pass_rate_table = build_pass_table(df_pass_rates)
pass_rate_table_fp = DIR_DATA / "pass_rate_table.tex"
pass_rate_table_fp.write_text(pass_rate_table)


# fig = plot_pass_rates_bar(df_pass_rates)
# fig.savefig(DIR_FIGURES / "pass_rates.png", dpi=300)

fig = plot_pass_rates_line(
    df_pass_rates,
    "Pass Rates for Agentic HLS Kernel Generation Task",
    ks=[1, 10],
)
fig.savefig(DIR_FIGURES / "pass_rates_line.png", dpi=300)


### Inference scaling analysis

ks = list(range(1, 10 + 1))
df_pass_rates_all = compute_pass_rates(df_pass, ks)
df_pass_rates_all.to_csv(DIR_DATA / "pass_rates_all.csv", index=False)

df_pass_rates_synth_only = df_pass_rates_all[
    df_pass_rates_all["metric_name"] == "pass_synth"
].copy()
# print(df_pass_rates_synth_only)


fig, ax = plt.subplots(figsize=(6, 3.5))

ax.grid(which="both", axis="both", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

ax.hlines(
    y=1.0,
    xmin=1,
    xmax=10,
    colors="black",
    linestyles="dashed",
)

for model_name in df_pass_rates_synth_only["model_name"].unique():
    df_model = df_pass_rates_synth_only[
        df_pass_rates_synth_only["model_name"] == model_name
    ]
    # sort by k
    df_model = df_model.sort_values("k")
    ks = df_model["k"].to_numpy()
    pass_rates = df_model["pass_rate"].to_numpy()
    ax.plot(
        ks,
        pass_rates,
        label=model_name_map[model_name],
        color=model_color_map[model_name],
    )

ax.set_xlabel("Number of Samples ($k$)")
ax.set_ylabel("Pass Rate at HLS Synthesis Stage")
ax.set_title("Agentic Inference Scaling of\nHLS Design Generation Task")
ax.legend(loc="lower center", ncol=2, fontsize="small")

ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels(
    [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
)  # format as percent in 10% increments

ax.set_ylim(0, 1.05)


ax.set_xlim(1, 10)
# only set labels at 1 and 10

ax.set_xscale("log")

ax.set_xticks([1, 10])
ax.set_xticklabels(["$10^0$", "$10^1$"])
# dont set minor tick labels
ax.set_xticklabels([], minor=True)

fig.tight_layout()
fig.savefig(DIR_FIGURES / "pass_rate_synth.png", dpi=300)

# compute the pass rate difference between 1 and 10 samples for each model

for model_name in df_pass_rates_synth_only["model_name"].unique():
    df_model = df_pass_rates_synth_only[
        df_pass_rates_synth_only["model_name"] == model_name
    ]
    pass_rate_1 = df_model[df_model["k"] == 1]["pass_rate"].values[0]
    pass_rate_10 = df_model[df_model["k"] == 10]["pass_rate"].values[0]
    pass_rate_diff = pass_rate_10 - pass_rate_1
    print(
        f"{model_name_map[model_name]}: Pass Rate at k=1: {pass_rate_1:.2%}, Pass Rate at k=10: {pass_rate_10:.2%}, Difference: {pass_rate_diff:.2%}"
    )
