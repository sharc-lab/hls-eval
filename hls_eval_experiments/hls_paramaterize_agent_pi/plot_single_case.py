import json
from pathlib import Path

import matplotlib.pyplot as plt

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data"

CASE_NAME = "2mm__deepseek_deepseek_v4_flash"
DIR_CASE = DIR_OUTPUT_DATA / CASE_NAME

DIR_FIGURES = DIR_CURRENT / "figures"


def make_plot_for_case(dir_case: Path):
    fp_all_eval_data_json = dir_case / "all_eval_data.json"
    eval_data = json.loads(fp_all_eval_data_json.read_text())

    n_rollouts = len(eval_data.keys())
    assert n_rollouts >= 1, f"Expected at least 1 rollout, but found {n_rollouts}"
    # only use the first one
    first_rollout_key = list(eval_data.keys())[0]
    eval_data_first = eval_data[first_rollout_key]

    baseline_point = eval_data_first["baseline"]

    # assert baseline_point["passed"] is True
    if not baseline_point["passed"]:
        raise ValueError(f"Baseline point did not pass for case {CASE_NAME}.")

    pareto_data_baseline = {
        "latency": baseline_point["vitis_hls_tool_out"]["data_tool"][
            "latency_worst_cycles"
        ],
        "resources_lut_used": baseline_point["vitis_hls_tool_out"]["data_tool"][
            "resources_lut_used"
        ],
        "resources_ff_used": baseline_point["vitis_hls_tool_out"]["data_tool"][
            "resources_ff_used"
        ],
        "resources_dsp_used": baseline_point["vitis_hls_tool_out"]["data_tool"][
            "resources_dsp_used"
        ],
        "resources_bram_used": baseline_point["vitis_hls_tool_out"]["data_tool"][
            "resources_bram_used"
        ],
    }

    # build the pareo point for each
    pareto_data_param = []
    for point in eval_data_first["points"]:
        # get point index
        point_index = point["point_index"]

        # assert point["render_success"] is True
        # assert point["passed"] is True
        if not point["passed"] or not point["render_success"]:
            print(
                f"Skipping point {point_index} for case {CASE_NAME} because it did not pass or render successfully."
            )
            continue

        point_data = {
            "point_index": point_index,
            "latency": point["vitis_hls_tool_out"]["data_tool"]["latency_worst_cycles"],
            "resources_lut_used": point["vitis_hls_tool_out"]["data_tool"][
                "resources_lut_used"
            ],
            "resources_ff_used": point["vitis_hls_tool_out"]["data_tool"][
                "resources_ff_used"
            ],
            "resources_dsp_used": point["vitis_hls_tool_out"]["data_tool"][
                "resources_dsp_used"
            ],
            "resources_bram_used": point["vitis_hls_tool_out"]["data_tool"][
                "resources_bram_used"
            ],
        }
        pareto_data_param.append(point_data)

    resource_types = {
        "resources_lut_used": ("LUTs Used", "resources_lut_total"),
        "resources_ff_used": ("FFs Used", "resources_ff_total"),
        "resources_dsp_used": ("DSPs Used", "resources_dsp_total"),
        "resources_bram_used": ("BRAMs Used", "resources_bram_total"),
    }
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    for ax, (resource_key, (resource_label, total_key)) in zip(
        axes.flat, resource_types.items()
    ):
        ax.scatter(
            [pareto_data_baseline[resource_key]],
            [pareto_data_baseline["latency"]],
            color="red",
            label="Baseline",
        )
        ax.scatter(
            [point[resource_key] for point in pareto_data_param],
            [point["latency"] for point in pareto_data_param],
            color="blue",
            label="Param",
            marker="x",
        )

        pareto_points = []
        for point in pareto_data_param:
            if not any(
                other[resource_key] <= point[resource_key]
                and other["latency"] <= point["latency"]
                and (
                    other[resource_key] < point[resource_key]
                    or other["latency"] < point["latency"]
                )
                for other in pareto_data_param
            ):
                pareto_points.append(point)
        pareto_points.sort(key=lambda point: point[resource_key])
        ax.plot(
            [point[resource_key] for point in pareto_points],
            [point["latency"] for point in pareto_points],
            color="green",
            label="Pareto Front",
            zorder=-5,
        )

        for point in pareto_data_param:
            ax.text(
                point[resource_key],
                point["latency"],
                f'{pareto_data_baseline["latency"] / point["latency"]:.2f}x',
                fontsize=8,
                verticalalignment="bottom",
                horizontalalignment="right",
            )

        total_resources = baseline_point["vitis_hls_tool_out"]["data_tool"][total_key]
        for pct in [1.0, 0.75, 0.5, 0.25, 0.1]:
            ax.axvline(
                total_resources * pct,
                color="gray",
                linestyle="--",
                label=f"{int(pct * 100)}% Total Available",
                zorder=-10,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(resource_label)
        ax.set_ylabel("Latency (cycles)")
        ax.set_title(resource_label)
        ax.legend(fontsize=8)
    fig.tight_layout()

    if not DIR_FIGURES.exists():
        DIR_FIGURES.mkdir()

    f_name = f"pareto_front__{CASE_NAME}.png"
    fp_fig = DIR_FIGURES / f_name
    fig.savefig(fp_fig, dpi=300)


if __name__ == "__main__":
    make_plot_for_case(DIR_CASE)
