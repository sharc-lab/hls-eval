import itertools
import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns


def pass_at_k(n: int, c: int, k: int) -> float:
    if n - c < k:
        return 1.0
    return float(1.0 - np.prod(1.0 - k / np.arange(n - c + 1, n + 1)))


metric_name_map = {
    "pass_parse": "Can Parse",
    "pass_compile": "Can Compile",
    "pass_tb": "Can Pass Testbench",
    "pass_synth": "Can Synthesize",
}


model_name_map = {
    "Qwen/Qwen2.5-Coder-32B-Instruct": "Qwen2.5 Coder 32B",
    "deepseek-ai/DeepSeek-V3": "DeepSeek V3",
    "meta-llama/Llama-3-70b-chat-hf": "Llama 3 70B",
    "meta-llama/Llama-3-8b-chat-hf": "Llama 3 8B",
    "google/gemini-2.0-flash-lite-001": "Gemini 2.0 Flash Lite",
}


model_color_map = {
    "Qwen/Qwen2.5-Coder-32B-Instruct": "#ef476f",
    "deepseek-ai/DeepSeek-V3": "#ffd166",
    "meta-llama/Llama-3-70b-chat-hf": "#06d6a0",
    "meta-llama/Llama-3-8b-chat-hf": "#118ab2",
    "google/gemini-2.0-flash-lite-001": "#65d16c",
}


def build_df_from_all_eval_json_files(all_eval_json_paths: list[Path]):
    rows = []
    df = pd.DataFrame(
        columns=[
            "eval_id",
            "benchmark_case_name",
            "benchmark_case_tags",
            "model_name",
            "eval_index",
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

    for eval_data_fp in all_eval_json_paths:
        eval_data_top = json.loads(eval_data_fp.read_text())

        for eval_index, eval_data in eval_data_top.items():
            df_row = {}
            df_row["eval_id"] = eval_data["eval_id"]
            df_row["benchmark_case_name"] = eval_data["benchmark_case_name"]
            df_row["model_name"] = eval_data["model_name"]
            df_row["benchmark_case_tags"] = eval_data["benchmark_case_tags"]

            df_row["eval_index"] = eval_index

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
                df_row["pass_tb"] = (
                    eval_data["c_run_out"]["data_execution"]["return_code"] == 0
                )

            if "vitis_hls_tool_out" not in eval_data:
                df_row["pass_synth"] = False
            else:
                df_row["pass_synth"] = (
                    eval_data["vitis_hls_tool_out"]["data_execution"]["return_code"]
                    == 0
                )

            if "llm_execution_time" in eval_data:
                df_row["exec_llm__t0"] = eval_data["llm_execution_time"]["t0"]
                df_row["exec_llm__t1"] = eval_data["llm_execution_time"]["t1"]
                df_row["exec_llm__dt"] = eval_data["llm_execution_time"][
                    "execution_time"
                ]
            else:
                df_row["exec_llm__t0"] = None
                df_row["exec_llm__t1"] = None
                df_row["exec_llm__dt"] = None

            if "c_compile_out" in eval_data:
                df_row["exec_compile__t0"] = eval_data["c_compile_out"][
                    "data_execution"
                ]["t0"]
                df_row["exec_compile__t1"] = eval_data["c_compile_out"][
                    "data_execution"
                ]["t1"]
                df_row["exec_compile__dt"] = eval_data["c_compile_out"][
                    "data_execution"
                ]["execution_time"]
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
                df_row["exec_synth__t0"] = eval_data["vitis_hls_tool_out"][
                    "data_execution"
                ]["t0"]
                df_row["exec_synth__t1"] = eval_data["vitis_hls_tool_out"][
                    "data_execution"
                ]["t1"]
                df_row["exec_synth__dt"] = eval_data["vitis_hls_tool_out"][
                    "data_execution"
                ]["execution_time"]
            else:
                df_row["exec_synth__t0"] = None
                df_row["exec_synth__t1"] = None
                df_row["exec_synth__dt"] = None

            rows.append(df_row)

    df = pd.concat([df, pd.DataFrame(rows)], ignore_index=True)
    return df


def compute_pass_rates(df: pd.DataFrame, ks=[1, 5]):
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

        for k in ks:
            pass_at_k_parse = pass_at_k(n_samples, n_pass_parse, k)
            pass_at_k_compile = pass_at_k(n_samples, n_pass_compile, k)
            pass_at_k_tb = pass_at_k(n_samples, n_pass_tb, k)
            pass_at_k_synth = pass_at_k(n_samples, n_pass_synth, k)

            pass_at_k_vals = {
                "pass_parse": pass_at_k_parse,
                "pass_compile": pass_at_k_compile,
                "pass_tb": pass_at_k_tb,
                "pass_synth": pass_at_k_synth,
            }

            for pass_at_k_key in pass_at_k_vals:
                data_pass_at_k.append(
                    {
                        "eval_id": eval_id,
                        "model_name": df_group["model_name"].iloc[0],
                        "benchmark_case_name": df_group["benchmark_case_name"].iloc[0],
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
            "metric_name",
            "k",
            "pass_rate",
        ],
    )
    # now what we want to do is for each (metric, k) we want to compute the avcge for each model over all evals
    df_agg = (
        df_new.groupby(["model_name", "metric_name", "k"])
        .agg({"pass_rate": "mean"})
        .reset_index()
    )

    return df_agg


def build_pass_table(df_pass_rates: pd.DataFrame):
    df_pass_rates = df_pass_rates.copy()
    df_pass_rates["model_name"] = df_pass_rates["model_name"].map(model_name_map)
    df_pass_rates["metric_name"] = df_pass_rates["metric_name"].map(metric_name_map)

    df_pass_rates = df_pass_rates.pivot_table(
        index=["model_name"],
        columns=[
            "metric_name",
            "k",
        ],
        values="pass_rate",
    )

    # sort metrics colums multi index in a specific order
    order_map = {
        "Can Parse": 0,
        "Can Compile": 1,
        "Can Pass Testbench": 2,
        "Can Synthesize": 3,
    }
    df_pass_rates = df_pass_rates.sort_index(axis=1, key=lambda x: x.map(order_map))

    # sort the models rows in a specifc order of models
    order_map = {
        "DeepSeek V3": 0,
        "Qwen2.5 Coder 32B": 1,
        "Llama 3 70B": 2,
        "Llama 3 8B": 3,
    }
    df_pass_rates = df_pass_rates.sort_values(
        by="model_name", key=lambda x: x.map(order_map)
    )

    df_pass_rates = df_pass_rates.fillna("")
    # df_pass_rates = df_pass_rates.rename_axis(None, axis=1)
    # df_pass_rates = df_pass_rates.rename_axis(None, axis=0)

    # repalce value sin k colum, 1 -> pass@1, 5 -> pass@5
    df_pass_rates.columns = pd.MultiIndex.from_tuples(
        [(metric, f"pass@{k}") for metric, k in df_pass_rates.columns]
    )

    latex_txt = df_pass_rates.to_latex(
        escape=True,
        multicolumn_format="c",
        multicolumn=True,
        float_format="{:0.1%}".format,
        # bold_rows=False,
    )
    # replace % with \%
    latex_txt = latex_txt.replace("%", r"\%")

    # replace metric_name with ""
    latex_txt = latex_txt.replace("metric_name", "")
    latex_txt = latex_txt.replace("model_name", "")

    # remove empty rows
    latex_txt = latex_txt.replace(" &  &  &  &  &  &  &  &  \\\\\n", "")

    # \begin{tabular}{l|rr|rr|rr|rr}
    latex_txt = latex_txt.replace("{lrrrrrrrr}\n", "{l|rr|rr|rr|rr}\n")

    latex_txt = latex_txt.replace(
        "multicolumn{2}{c}{Can Compile}",
        "multicolumn{2}{c|}{Can Compile}",
    )
    latex_txt = latex_txt.replace(
        "multicolumn{2}{c}{Can Parse}",
        "multicolumn{2}{c|}{Can Parse}",
    )
    latex_txt = latex_txt.replace(
        "multicolumn{2}{c}{Can Pass Testbench}",
        "multicolumn{2}{c|}{Can Pass Testbench}",
    )

    # find this line
    # "& pass@1 & pass@5 & pass@1 & pass@5 & pass@1 & pass@5 & pass@1 & pass@5 \\"
    # and insert this above it
    #  \cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}
    lines = latex_txt.splitlines()
    for i, line in enumerate(lines):
        if (
            "& pass@1 & pass@5 & pass@1 & pass@5 & pass@1 & pass@5 & pass@1 & pass@5 \\"
            in line
        ):
            lines.insert(
                i,
                # r"\cmidrule(lr){2-3} \cmidrule(lr){4-5} \cmidrule(lr){6-7} \cmidrule(lr){8-9}",
                r"\midrule",
            )
            break
    latex_txt = "\n".join(lines)

    # Can Pass Testbench -> Can Pass TB
    latex_txt = latex_txt.replace("Can Pass Testbench", r"Can Pass TB")
    # Can Synthesize -> Can Synth
    latex_txt = latex_txt.replace("Can Synthesize", r"Can Synth")

    # replace \toprule with \cmidrule[\heavyrulewidth]{2-9}
    latex_txt = latex_txt.replace("\\toprule", r"\cmidrule[\heavyrulewidth]{2-9}")

    latex_txt = latex_txt.replace("& pass@1", "Model & pass@1", 1)

    # bold Model, pass@1, pass@5, Can Parse, Can Compile, Can Pass Testbench, Can Synthesize
    latex_txt = latex_txt.replace("Model", r"\textbf{Model}")
    latex_txt = latex_txt.replace("pass@1", r"\textbf{pass@1}")
    latex_txt = latex_txt.replace("pass@5", r"\textbf{pass@5}")
    latex_txt = latex_txt.replace("Can Parse", r"\textbf{Can Parse}")
    latex_txt = latex_txt.replace("Can Compile", r"\textbf{Can Compile}")
    latex_txt = latex_txt.replace("Can Pass TB", r"\textbf{Can Pass TB}")
    latex_txt = latex_txt.replace("Can Synth", r"\textbf{Can Synth}")

    # replace all

    return latex_txt


def plot_pass_rates_bar(df_pass_rates, ks=[1, 5]):
    models = df_pass_rates["model_name"].unique()

    fig, axs = plt.subplots(len(ks), 1, figsize=(8, 6), sharex=True)

    for k, ax in zip(ks, axs):
        df_filtered = df_pass_rates[df_pass_rates["k"] == k]
        df_melt = df_filtered
        ax.grid(axis="y", linestyle="--", alpha=0.8, zorder=-10)
        ax.set_axisbelow(True)

        ax.hlines(
            y=1,
            color="black",
            linestyle="--",
            xmin=-0.5,
            xmax=len(df_melt["model_name"].unique()) - 0.5,
        )

        sns.barplot(
            x="model_name",
            y="pass_rate",
            hue="metric_name",
            hue_order=["pass_parse", "pass_compile", "pass_tb", "pass_synth"],
            data=df_melt,
            ax=ax,
            zorder=10,
        )

        ax.set_ylim(0, 1.2)

        ax.set_yticks(np.arange(0, 1.1, 0.1))
        ax.set_yticklabels(
            [f"{x:.0%}" for x in np.arange(0, 1.1, 0.1)]
        )  # format as percent in 10% increments
        ax.set_title("pass@k={}".format(k))

        current_x_ticks = ax.get_xticks()
        ax.set_xticks(current_x_ticks)
        ax.set_xticklabels(
            [model_name_map[model] for model in models], rotation=0, ha="center"
        )
        ax.legend(
            [
                metric_name_map[metric]
                for metric in ["pass_parse", "pass_compile", "pass_tb", "pass_synth"]
            ],
            loc="upper center",
            ncol=4,
        )

    fig.suptitle('Pass Rate of Zero-Shot Editing for "Loop Tiling" Task by Model')

    fig.tight_layout()
    return fig


def plot_pass_rates_line(df_pass_rates, title: str, ks=[1, 5], leg_ncols: int = 2):
    models = df_pass_rates["model_name"].unique()
    n_models = len(models)
    # colors = matplotlib.cm.tab20(range(20))
    # cm = plt.get_cmap("tab20")
    # model_to_color = {model: cm(i) for i, model in enumerate(models)}

    model_to_color = {model: model_color_map[model] for model in models}

    fig, ax = plt.subplots(1, 1, figsize=(6, 3.5))

    ax.grid(axis="y", linestyle="--", alpha=0.8, zorder=-10)
    ax.set_axisbelow(True)

    coord_to_stage = {
        0: "pass_parse",
        1: "pass_compile",
        2: "pass_tb",
        3: "pass_synth",
    }

    models = df_pass_rates["model_name"].unique()
    combos = list(itertools.product(models, ks))

    for model, k in combos:
        df_filtered = df_pass_rates[
            (df_pass_rates["model_name"] == model) & (df_pass_rates["k"] == k)
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
        color = model_to_color[model]
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
            label=f"{model_name_map[model]} - pass@{k}",
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
