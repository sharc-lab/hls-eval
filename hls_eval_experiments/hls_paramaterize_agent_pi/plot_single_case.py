import json
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.transforms import blended_transform_factory

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data"

DIR_FIGURES = DIR_CURRENT / "figures"


def make_plot_for_case(dir_case: Path):
    case_name = dir_case.name
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
        raise ValueError(f"Baseline point did not pass for case {case_name}.")

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
                f"Skipping point {point_index} for case {case_name} because it did not pass or render successfully."
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
    fig, axes = plt.subplots(2, 2, figsize=(14, 7))
    for ax, (resource_key, (resource_label, total_key)) in zip(
        axes.flat, resource_types.items()
    ):
        all_values = [pareto_data_baseline[resource_key]] + [
            point[resource_key] for point in pareto_data_param
        ]
        if all(value == 0 for value in all_values):
            ax.text(
                0.5,
                0.5,
                f"No {resource_label}",
                fontsize=14,
                horizontalalignment="center",
                verticalalignment="center",
                transform=ax.transAxes,
            )
            ax.set_xlabel(resource_label)
            ax.set_ylabel("Latency (cycles)")
            ax.set_title(resource_label)
            continue

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
        if len(pareto_points) == 1:
            ax.plot(
                [point[resource_key] for point in pareto_points],
                [point["latency"] for point in pareto_points],
                color="green",
                label="Pareto Front",
                marker="o",
                markersize=20,
                markerfacecolor="green",
                markeredgecolor="green",
                alpha=0.3,
                linestyle="none",
                zorder=-5,
            )
        else:
            ax.plot(
                [point[resource_key] for point in pareto_points],
                [point["latency"] for point in pareto_points],
                color="green",
                label="Pareto Front",
                marker="o",
                markersize=6,
                zorder=-5,
            )

        for point in pareto_data_param:
            ax.text(
                point[resource_key],
                point["latency"],
                f"{pareto_data_baseline['latency'] / point['latency']:.2f}x",
                fontsize=8,
                verticalalignment="bottom",
                horizontalalignment="right",
            )

        total_resources = baseline_point["vitis_hls_tool_out"]["data_tool"][total_key]
        vline_transform = blended_transform_factory(ax.transData, ax.transAxes)
        for pct in [1.0, 0.75, 0.5, 0.25, 0.1]:
            vline_x = total_resources * pct
            ax.axvline(
                vline_x,
                color="gray",
                linestyle="--",
                zorder=-10,
            )
            ax.text(
                vline_x,
                0.9,
                f"{int(pct * 100)}%",
                transform=vline_transform,
                fontsize=8,
                color="black",
                rotation=90,
                horizontalalignment="center",
                verticalalignment="center",
                bbox={
                    "boxstyle": "round,pad=0.2",
                    "facecolor": "white",
                    "edgecolor": "black",
                    "linewidth": 0.5,
                },
                zorder=-9,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        ax.set_xlabel(resource_label)
        ax.set_ylabel("Latency (cycles)")
        ax.set_title(resource_label)
        legend = ax.legend(fontsize=8)
        for legend_handle in legend.legend_handles:
            if legend_handle.get_label() == "Pareto Front":
                legend_handle.set_markersize(6)
    fig.tight_layout()

    if not DIR_FIGURES.exists():
        DIR_FIGURES.mkdir()

    f_name = f"pareto_front__{case_name}.png"
    fp_fig = DIR_FIGURES / f_name
    fig.savefig(fp_fig, dpi=300)


if __name__ == "__main__":
    dir_cases_plot = []

    all_dir_cases = list(DIR_OUTPUT_DATA.iterdir())
    for dir_case in all_dir_cases:
        if not dir_case.is_dir():
            continue

        # check if the dir has a all_eval_data.json file
        fp_all_eval_data_json = dir_case / "all_eval_data.json"
        if not fp_all_eval_data_json.exists():
            print(
                f"Skipping {dir_case} because it does not have an all_eval_data.json file."
            )
            continue

        dir_cases_plot.append(dir_case)

    for dir_case in dir_cases_plot:
        print(f"Making plot for case {dir_case.name}...")
        make_plot_for_case(dir_case)
