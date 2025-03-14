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


df_pass_rates = compute_pass_rates(df_pass)
df_pass_rates.to_csv(DIR_DATA / "pass_rates.csv", index=False)


pass_rate_table = build_pass_table(df_pass_rates)
pass_rate_table_fp = DIR_DATA / "pass_rate_table.tex"
pass_rate_table_fp.write_text(pass_rate_table)


fig = plot_pass_rates_bar(df_pass_rates)
fig.savefig(DIR_FIGURES / "pass_rates.png", dpi=300)


fig = plot_pass_rates_line(
    df_pass_rates, "Pass Rate of Zero-Shot Editing by Model: Loop Labeling"
)
fig.savefig(DIR_FIGURES / "pass_rates_line.png", dpi=300)
