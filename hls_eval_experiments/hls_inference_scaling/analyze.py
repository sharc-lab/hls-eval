import itertools
import json
from pathlib import Path
from pprint import pprint

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
DIR_INPUT_DATA = DIR_CURRENT / "output_data_backup"

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

ks = list(range(1, 40 + 1))
df_pass_rates = compute_pass_rates(df_pass, ks)
df_pass_rates.to_csv(DIR_DATA / "pass_rates.csv", index=False)


df_pass_rates_synth_only = df_pass_rates[
    df_pass_rates["metric_name"] == "pass_synth"
].copy()
print(df_pass_rates_synth_only)

# for each model make a line plot where x is k and y is pass rate

fig, ax = plt.subplots(figsize=(5, 4))

ax.grid(which="both", axis="both", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

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
ax.set_title("Inference Scaling of HLS Editing Task:\nDataflow Refactoring")
ax.legend(loc="upper center", ncol=2, fontsize="small")

ax.set_yticks(np.arange(0, 1.1, 0.1))
ax.set_yticklabels(
    [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
)  # format as percent in 10% increments

ax.set_ylim(0, 1.05)


ax.set_xlim(1, 40)
ax.set_xscale("log")

fig.tight_layout()
fig.savefig(DIR_FIGURES / "pass_rate_synth.png", dpi=300)
