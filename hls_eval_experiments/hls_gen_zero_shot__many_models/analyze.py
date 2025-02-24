import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from matplotlib.axes import Axes
from matplotlib.figure import Figure
from matplotlib.transforms import blended_transform_factory

DIR_CURRENT = Path(__file__).resolve().parent
DIR_CURRENT_OUTPUT_DATA = DIR_CURRENT / "output_data"
if not DIR_CURRENT_OUTPUT_DATA.exists():
    DIR_CURRENT_OUTPUT_DATA.mkdir()

# single_eval_data.json
df = pd.DataFrame(
    columns=[
        "eval_id",
        "benchmark_case_name",
        "benchmark_case_tags",
        "model_name",
        "pass_parse",
        "pass_compile",
        "pass_tb",
        "pass_synth",
        "exec_llm__t0",
        "exec_llm__t1",
        "exec_llm__dt",
        "exec_llm__return_code",
        "exec_compile__t0",
        "exec_compile__t1",
        "exec_compile__dt",
        "exec_tb__t0",
        "exec_tb__t1",
        "exec_tb__dt",
        "exec_synth__t0",
        "exec_synth__t1",
        "exec_synth__dt",
    ]
)


# count how many are missing the single_eval_data.json
missing = []
for eval_case_run_dir in DIR_CURRENT_OUTPUT_DATA.iterdir():
    eval_data_fp = eval_case_run_dir / "single_eval_data.json"
    if not eval_data_fp.exists():
        missing.append(eval_case_run_dir.name)
print(f"Missing {len(missing)} evals")
print(missing)

if len(missing) > 0:
    raise ValueError(f"Missing {len(missing)} evals")

rows = []

for eval_case_run_dir in DIR_CURRENT_OUTPUT_DATA.iterdir():
    eval_data_fp = eval_case_run_dir / "single_eval_data.json"
    eval_data = json.loads(eval_data_fp.read_text())

    df_row = {}
    df_row["eval_id"] = eval_data["eval_id"]
    df_row["benchmark_case_name"] = eval_data["benchmark_case_name"]
    df_row["model_name"] = eval_data["model_name"]
    df_row["benchmark_case_tags"] = eval_data["benchmark_case_tags"]

    if "can_parse_output" not in eval_data:
        df_row["pass_parse"] = False
    else:
        df_row["pass_parse"] = eval_data["can_parse_output"]

    if "c_compile_out" not in eval_data:
        df_row["pass_compile"] = False
    else:
        df_row["pass_compile"] = (
            eval_data["c_compile_out"]["data_execution"]["return_code"] == 0
        )

    if "c_run_out" not in eval_data:
        df_row["pass_tb"] = False
    else:
        df_row["pass_tb"] = eval_data["c_run_out"]["data_execution"]["return_code"] == 0

    if "vitis_hls_tool_out" not in eval_data:
        df_row["pass_synth"] = False
    else:
        df_row["pass_synth"] = (
            eval_data["vitis_hls_tool_out"]["data_execution"]["return_code"] == 0
        )

    if "llm_execution_time" in eval_data:
        df_row["exec_llm__t0"] = eval_data["llm_execution_time"]["t0"]
        df_row["exec_llm__t1"] = eval_data["llm_execution_time"]["t1"]
        df_row["exec_llm__dt"] = eval_data["llm_execution_time"]["execution_time"]
    else:
        df_row["exec_llm__t0"] = None
        df_row["exec_llm__t1"] = None
        df_row["exec_llm__dt"] = None

    if "c_compile_out" in eval_data:
        df_row["exec_compile__t0"] = eval_data["c_compile_out"]["data_execution"]["t0"]
        df_row["exec_compile__t1"] = eval_data["c_compile_out"]["data_execution"]["t1"]
        df_row["exec_compile__dt"] = eval_data["c_compile_out"]["data_execution"][
            "execution_time"
        ]
    else:
        df_row["exec_compile__t0"] = None
        df_row["exec_compile__t1"] = None
        df_row["exec_compile__dt"] = None

    if "c_run_out" in eval_data:
        df_row["exec_tb__t0"] = eval_data["c_run_out"]["data_execution"]["t0"]
        df_row["exec_tb__t1"] = eval_data["c_run_out"]["data_execution"]["t1"]
        df_row["exec_tb__dt"] = eval_data["c_run_out"]["data_execution"][
            "execution_time"
        ]
    else:
        df_row["exec_tb__t0"] = None
        df_row["exec_tb__t1"] = None
        df_row["exec_tb__dt"] = None

    if "vitis_hls_tool_out" in eval_data:
        df_row["exec_synth__t0"] = eval_data["vitis_hls_tool_out"]["data_execution"][
            "t0"
        ]
        df_row["exec_synth__t1"] = eval_data["vitis_hls_tool_out"]["data_execution"][
            "t1"
        ]
        df_row["exec_synth__dt"] = eval_data["vitis_hls_tool_out"]["data_execution"][
            "execution_time"
        ]
    else:
        df_row["exec_synth__t0"] = None
        df_row["exec_synth__t1"] = None
        df_row["exec_synth__dt"] = None

    rows.append(df_row)


df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
# print num of rows
print(df.shape[0])
df_pass = df[
    [
        "eval_id",
        "benchmark_case_name",
        "benchmark_case_tags",
        "model_name",
        "pass_parse",
        "pass_compile",
        "pass_tb",
        "pass_synth",
    ]
]

# plot pass rate by model

metric_name_map = {
    "pass_parse": "Can Parse",
    "pass_compile": "Can Compile",
    "pass_tb": "Can Pass Testbench",
    "pass_synth": "Can Synthesize",
}


model_name_map = {
    "Qwen/Qwen2.5-Coder-32B-Instruct": "Qwen2.5 Coder 32B",
    "google/gemma-2-27b-it": "Gemma 2 27B",
    "meta-llama/Llama-3-70b-chat-hf": "Llama 3 70B",
    "meta-llama/Llama-3-8b-chat-hf": "Llama 3 8B",
}


def plot_pass_rate(df_pass: pd.DataFrame):
    models = df_pass["model_name"].unique()
    pass_rates_agg = {}
    for model in models:
        df_model = df_pass[df_pass["model_name"] == model]
        pass_rates_agg[model] = (
            df_model[["pass_parse", "pass_compile", "pass_tb", "pass_synth"]]
            .mean()
            .to_dict()
        )

    df_pass_agg = (
        pd.DataFrame(pass_rates_agg).T.reset_index().rename(columns={"index": "model"})
    )
    df_pass_agg = df_pass_agg.melt(
        id_vars=["model"], var_name="metric", value_name="pass_rate"
    )
    print(df_pass_agg)

    models = df_pass_agg["model"].unique()

    fig, ax = plt.subplots(figsize=(8, 4))

    ax.grid(axis="y", linestyle="--", alpha=0.8, zorder=-10)
    ax.set_axisbelow(True)

    ax.hlines(y=1, color="black", linestyle="--", xmin=-0.5, xmax=len(models) - 0.5)

    sns.barplot(
        x="model",
        y="pass_rate",
        hue="metric",
        hue_order=["pass_parse", "pass_compile", "pass_tb", "pass_synth"],
        data=df_pass_agg,
        ax=ax,
        zorder=10,
    )

    ax.set_ylim(0, 1.2)

    ax.set_yticks(np.arange(0, 1.1, 0.1))
    ax.set_yticklabels(
        [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
    )  # format as percent in 10% increments
    ax.set_title("Pass Rate of Zero-Shot HLS Generation by Model")

    current_x_ticks = ax.get_xticks()
    ax.set_xticks(current_x_ticks)
    ax.set_xticklabels(
        [model_name_map[model] for model in models], rotation=0, ha="center"
    )

    fig.tight_layout()
    ax.legend(
        [
            metric_name_map[metric]
            for metric in ["pass_parse", "pass_compile", "pass_tb", "pass_synth"]
        ],
        loc="upper center",
        ncol=4,
    )
    return fig


fig = plot_pass_rate(df_pass)
FIG_DIR = DIR_CURRENT / "output_figures"
FIG_DIR.mkdir(exist_ok=True)
fig.savefig(FIG_DIR / "pass_rate_plot.png", dpi=300)


def plot_pass_rate_grouped(df_pass: pd.DataFrame, group_tags: list[str]):
    # print(df_pass)
    # print the typeof the benchmark_case_name column
    # print(df_pass["benchmark_case_name"].dtype)
    tag_map: dict[str, pd.DataFrame] = {}
    for tag in group_tags:
        tag_map[tag] = df_pass[df_pass["benchmark_case_tags"].apply(lambda x: tag in x)]

    pass_rates_agg: dict[str, dict[str, dict[str, float]]] = {}
    for tag, df_tag in tag_map.items():
        models = df_tag["model_name"].unique()
        pass_rates_agg[tag] = {}
        for model in models:
            df_model = df_tag[df_tag["model_name"] == model]
            pass_rates_agg[tag][model] = (
                df_model[["pass_parse", "pass_compile", "pass_tb", "pass_synth"]]
                .mean()
                .to_dict()
            )

    df_pass_aggs = {}
    for tag, pass_rates in pass_rates_agg.items():
        df_pass_agg = (
            pd.DataFrame(pass_rates).T.reset_index().rename(columns={"index": "model"})
        )
        df_pass_agg["tag"] = tag
        df_pass_aggs[tag] = df_pass_agg

    fig, axs = plt.subplots(
        len(group_tags),
        1,
        figsize=(8, 6),
    )

    for idx, (tag, ax) in enumerate(zip(group_tags, axs)):
        df_pass_agg = df_pass_aggs[tag]
        df_pass_agg = df_pass_agg.melt(
            id_vars=["model", "tag"], var_name="metric", value_name="pass_rate"
        )

        models = df_pass_agg["model"].unique()

        ax.grid(axis="y", linestyle="--", alpha=0.8, zorder=-10)
        ax.set_axisbelow(True)

        ax.hlines(y=1, color="black", linestyle="--", xmin=-0.5, xmax=len(models) - 0.5)

        sns.barplot(
            x="model",
            y="pass_rate",
            hue="metric",
            hue_order=["pass_parse", "pass_compile", "pass_tb", "pass_synth"],
            data=df_pass_agg,
            ax=ax,
            zorder=10,
        )

        ax.set_ylim(0, 1.2)

        ax.set_yticks(np.arange(0, 1.1, 0.1))
        ax.set_yticklabels(
            [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
        )  # format as percent in 10% increments

        current_x_ticks = ax.get_xticks()
        ax.set_xticks(current_x_ticks)
        ax.set_xticklabels(
            [model_name_map[model] for model in models], rotation=0, ha="center"
        )

        fig.tight_layout()
        ax.legend(
            [
                metric_name_map[metric]
                for metric in ["pass_parse", "pass_compile", "pass_tb", "pass_synth"]
            ],
            loc="upper center",
            ncol=4,
        )

        ax.set_title(f"Benchmark Set: {tag}")

    fig.suptitle("Pass Rate of Zero-Shot HLS Generation by Model")
    fig.tight_layout()
    return fig


fig = plot_pass_rate_grouped(df_pass, group_tags=["polybench", "c2hlsc"])
FIG_DIR = DIR_CURRENT / "output_figures"
FIG_DIR.mkdir(exist_ok=True)
fig.savefig(FIG_DIR / "pass_rate_plot_grouped.png", dpi=300)


exit()


df_exec = df[
    [
        "eval_id",
        "benchmark_case_name",
        "model_name",
        "exec_llm__t0",
        "exec_llm__t1",
        "exec_llm__dt",
        "exec_compile__t0",
        "exec_compile__t1",
        "exec_compile__dt",
        "exec_tb__t0",
        "exec_tb__t1",
        "exec_tb__dt",
        "exec_synth__t0",
        "exec_synth__t1",
        "exec_synth__dt",
    ]
]


def compute_utilization(
    events, n_steps, min_time: float | None = None, max_time: float | None = None
):
    """
    Compute utilization at n_steps time points between the earliest start and latest stop.

    Args:
        events (list of tuple): Each tuple is (start_time, stop_time)
        n_steps (int): Number of time points (including endpoints) at which to compute utilization.

    Returns:
        time_steps (numpy.ndarray): Array of time points.
        utilization (list): List of utilization values at each time point.
    """
    # Determine the overall start and stop times
    # min_time = min(start for start, _ in events)
    if min_time is None:
        min_time_set = min(start for start, _ in events)
    else:
        min_time_set = min_time
    # max_time = max(stop for _, stop in events)
    if max_time is None:
        # max_time = max(stop for _, stop in events)
        max_time_set = max(stop for _, stop in events)
    else:
        max_time_set = max_time

    # Create evenly spaced time steps between min_time and max_time
    time_steps = np.linspace(min_time_set, max_time_set, n_steps)
    utilization = []

    # For each time step, count how many events are active.
    # We assume an event is active if start <= t < stop.
    for t in time_steps:
        count = sum(1 for start, stop in events if start <= t < stop)
        utilization.append(count)

    return time_steps, utilization


def build_timeline_plot(df_exec: pd.DataFrame, n_steps: int = 50) -> Figure:
    min_time_pre = min(
        df_exec["exec_llm__t0"].min(),
        df_exec["exec_compile__t0"].min(),
        df_exec["exec_tb__t0"].min(),
        df_exec["exec_synth__t0"].min(),
    )

    df_exec.loc[:, "exec_llm__t0"] = df_exec["exec_llm__t0"] - min_time_pre
    df_exec.loc[:, "exec_llm__t1"] = df_exec["exec_llm__t1"] - min_time_pre
    df_exec.loc[:, "exec_compile__t0"] = df_exec["exec_compile__t0"] - min_time_pre
    df_exec.loc[:, "exec_compile__t1"] = df_exec["exec_compile__t1"] - min_time_pre
    df_exec.loc[:, "exec_tb__t0"] = df_exec["exec_tb__t0"] - min_time_pre
    df_exec.loc[:, "exec_tb__t1"] = df_exec["exec_tb__t1"] - min_time_pre
    df_exec.loc[:, "exec_synth__t0"] = df_exec["exec_synth__t0"] - min_time_pre
    df_exec.loc[:, "exec_synth__t1"] = df_exec["exec_synth__t1"] - min_time_pre

    # sort all the start times in a single list
    # print(
    all_start_times = sorted(
        list(df_exec["exec_llm__t0"])
        + list(df_exec["exec_compile__t0"])
        + list(df_exec["exec_tb__t0"])
        + list(df_exec["exec_synth__t0"])
    )
    # compute the gap sizes and if there are any gaps over 10 minutes remove any events that occur after the first gap
    gaps = [
        (all_start_times[i + 1] - all_start_times[i])
        for i in range(len(all_start_times) - 1)
    ]
    gaps = [0] + gaps
    gap_indices = [i for i, gap in enumerate(gaps) if gap > 60 * 8]
    if len(gap_indices) > 0:
        first_gap_idx = gap_indices[0]
        first_gap_time = all_start_times[first_gap_idx]
        df_exec = df_exec[
            (df_exec["exec_llm__t0"] < first_gap_time)
            & (df_exec["exec_compile__t0"] < first_gap_time)
            & (df_exec["exec_tb__t0"] < first_gap_time)
            & (df_exec["exec_synth__t0"] < first_gap_time)
        ]

    min_time = min(
        df_exec["exec_llm__t0"].min(),
        df_exec["exec_compile__t0"].min(),
        df_exec["exec_tb__t0"].min(),
        df_exec["exec_synth__t0"].min(),
    )

    max_time = max(
        df_exec["exec_llm__t1"].max(),
        df_exec["exec_compile__t1"].max(),
        df_exec["exec_tb__t1"].max(),
        df_exec["exec_synth__t1"].max(),
    )

    events_llm = []
    events_csim = []
    events_synth = []

    for _, row in df_exec.iterrows():
        if row["exec_llm__dt"] is not None:
            events_llm.append((row["exec_llm__t0"], row["exec_llm__t1"]))
        if row["exec_compile__dt"] is not None:
            events_csim.append((row["exec_compile__t0"], row["exec_compile__t1"]))
        if row["exec_synth__dt"] is not None:
            events_synth.append((row["exec_synth__t0"], row["exec_synth__t1"]))
        if row["exec_tb__dt"] is not None:
            events_csim.append((row["exec_tb__t0"], row["exec_tb__t1"]))

    time_steps_llm, utilization_llm = compute_utilization(
        events_llm, n_steps, min_time=min_time, max_time=max_time
    )
    time_steps_csim, utilization_csim = compute_utilization(
        events_csim, n_steps, min_time=min_time, max_time=max_time
    )
    time_steps_synth, utilization_synth = compute_utilization(
        events_synth, n_steps, min_time=min_time, max_time=max_time
    )

    pool_size = {
        "llm": 4,
        "csim": 8,
        "synth": 12,
    }
    realtive_sizes = {
        "llm": 4,
        "csim": 8,
        "synth": 12,
    }

    pool_labels = {
        "llm": "LLM Inference",
        "csim": "C Simulation",
        "synth": "HLS Synthesis",
    }

    n_rows = len(df_exec)

    fig, axs = plt.subplots(
        3,
        1,
        figsize=(6, 4),
        # sharex=True,
        gridspec_kw={"hspace": 0.05},
        height_ratios=[
            realtive_sizes[pool_type] for pool_type in ["llm", "csim", "synth"]
        ],
        # scale the height of each ax proportionally
    )
    axs: list[Axes]

    for idx, (ax, time_steps, utilization, pool_type) in enumerate(
        zip(
            axs,
            [time_steps_llm, time_steps_csim, time_steps_synth],
            [utilization_llm, utilization_csim, utilization_synth],
            ["llm", "csim", "synth"],
        )
    ):
        # add horizontal grid only
        ax.grid(axis="y", linestyle="--", alpha=0.5)
        # move to background
        ax.set_axisbelow(True)

        ax.fill_between(time_steps, utilization, step="post", alpha=0.5)
        ax.plot(time_steps, utilization, drawstyle="steps-post")

        # add text box in upper irght corner with Pool name
        ax.text(
            0.98,
            pool_size[pool_type] - 0.2,
            f"{pool_labels[pool_type]} (n_jobs={pool_size[pool_type]})",
            fontdict={"fontsize": 8},
            horizontalalignment="right",
            verticalalignment="center",
            transform=blended_transform_factory(ax.transAxes, ax.transData),
            bbox=dict(facecolor="white", alpha=1.0, edgecolor="gray", linewidth=1.0),
        )
        # ax.text(
        #     0.98,
        #     0.8,
        #     f"{pool_labels[pool_type]} (n_jobs={pool_size[pool_type]})",
        #     horizontalalignment="right",
        #     verticalalignment="center",
        #     transform=ax.transAxes,
        #     bbox=dict(facecolor="white", alpha=1.0, edgecolor="gray", linewidth=1.0),
        # )

        if idx == len(axs) - 1:
            ax.set_xlabel("Time (s)")

        # ax.set_ylabel(f"Pool Util.\n({pool_type})")
        # ax.set_ylabel(f"Pool Util.\n({pool_labels[pool_type]})")

        ax.set_xlim(min_time, max_time)
        if idx == len(axs) - 1:
            # set 15s ticks
            step_size = 30
            ax.set_xticks(np.arange(min_time, max_time, step_size))
            ax.set_xticklabels(
                [f"{x:.0f}" for x in np.arange(min_time, max_time, step_size)]
            )
        else:
            ax.set_xlabel(None)
            ax.set_xticks([])
            ax.set_xticklabels([])

        ax.set_ylim(
            0,
            pool_size[pool_type]
            + (pool_size[pool_type] / realtive_sizes[pool_type]) * 1.5,
        )
        ax.hlines(
            y=pool_size[pool_type],
            xmin=min_time,
            xmax=max_time,
            color="red",
            linestyle="--",
        )
        ax.set_yticks(np.arange(0, pool_size[pool_type] + 1, 1))
        ax.set_yticklabels(
            [None] + [f"{x:.0f}" for x in np.arange(1, pool_size[pool_type] + 1, 1)]
        )

        # remove every odd numbered y-tick label
        for label in ax.yaxis.get_ticklabels()[1::2]:
            label.set_visible(False)

    fig.suptitle(
        f"Timeline of Parallel Evalutation for\nZero-Shot HLS Generation of {n_rows} Design Runs"
    )

    fig.tight_layout()
    fig.subplots_adjust(left=0.09, top=0.88)
    fig.text(0.01, 0.5, "Pool Utilization", va="center", rotation="vertical")

    return fig


fig = build_timeline_plot(df_exec, n_steps=500)
FIG_DIR = DIR_CURRENT / "output_figures"
FIG_DIR.mkdir(exist_ok=True)
fig.savefig(FIG_DIR / "timeline_plot.png", dpi=300)
