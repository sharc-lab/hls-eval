from pathlib import Path

import pandas as pd

# bench_stats.csv

DIR_CURRENT = Path(__file__).parent
DIR_DATA = DIR_CURRENT / "exp_data"

data_fp = DIR_DATA / "bench_stats.csv"
df = pd.read_csv(data_fp)

# sum the kernel_loc col
print(f"Total kernel_loc: {df['kernel_loc'].sum()}")

# total synth runtime
data_synth_fp = DIR_DATA / "synth_runtimes.csv"
df_synth = pd.read_csv(data_synth_fp)

# print total synthesis time, synth_runtime
print(f"Total synthesis time: {df_synth['synth_runtime'].sum()}")
# in minutes
print(f"Total synthesis time: {df_synth['synth_runtime'].sum() / 60}")

# wrote to txt file

agg_stats_txt = ""
agg_stats_txt += f"Total kernel_loc: {df['kernel_loc'].sum()}\n"
agg_stats_txt += f"Total synthesis time: {df_synth['synth_runtime'].sum()}\n"
agg_stats_txt += (
    f"Total synthesis time (in minutes): {df_synth['synth_runtime'].sum() / 60}\n"
)
(agg_stats_fp := DIR_DATA / "agg_stats.txt").write_text(agg_stats_txt)
print(f"Aggregated stats written to: {agg_stats_fp}")
