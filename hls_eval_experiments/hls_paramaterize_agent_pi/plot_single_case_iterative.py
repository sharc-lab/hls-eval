import colorsys
import json
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

from plot_style_trj import apply_trj_style, source_label

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data_v2_big_run"

DIR_FIGURES = DIR_CURRENT / "figures"

# set matplotlib to use 'Agg' backend for headless environments
plt.switch_backend("Agg")

RESOURCE_TYPES = {
    "resources_lut_used": ("LUTs Used", "resources_lut_total"),
    "resources_ff_used": ("FFs Used", "resources_ff_total"),
    "resources_dsp_used": ("DSPs Used", "resources_dsp_total"),
    "resources_bram_used": ("BRAMs Used", "resources_bram_total"),
}

# Iteration point markers, cycled if there are more iterations than markers, so
# overlapping points from different iterations can be told apart by shape as
# well as color.
ITERATION_MARKERS = ["x", "+", "1", "2", "3", "4", "P", "*"]

# Axes-fraction heights the resource-budget labels alternate between, going
# from the smallest budget (10%) to the largest (100%): 10% high, 25% low,
# 50% high, 75% low, 100% high. Neighbors only collide where their lines are
# closer than a label's width, so the gap can be smaller than a label's height.
LABEL_Y_ROWS = [0.9, 0.72]

# Figure-fraction top of the axes grid, under the title / subtitle / legend.
AXES_TOP = 0.85


def _iteration_color(fraction: float):
    """Blue -> cyan -> green as fraction goes 0 -> 1, swept through hue space
    (rather than plain RGB interpolation) so intermediate iterations stay
    visually distinct instead of collapsing into a similar muddy teal."""
    hue_degrees = 240 - 120 * fraction
    return colorsys.hsv_to_rgb(hue_degrees / 360.0, 0.85, 0.9)


def _extract_point(point: dict) -> dict:
    metrics = point["vitis_hls_tool_out"]["data_tool"]
    return {
        "point_index": point.get("point_index"),
        "latency": metrics["latency_worst_cycles"],
        "resources_lut_used": metrics["resources_lut_used"],
        "resources_ff_used": metrics["resources_ff_used"],
        "resources_dsp_used": metrics["resources_dsp_used"],
        "resources_bram_used": metrics["resources_bram_used"],
    }


def _pareto_front(points: list[dict], resource_key: str) -> list[dict]:
    front = [
        point
        for point in points
        if not any(
            other[resource_key] <= point[resource_key]
            and other["latency"] <= point["latency"]
            and (
                other[resource_key] < point[resource_key]
                or other["latency"] < point["latency"]
            )
            for other in points
        )
    ]
    front.sort(key=lambda point: point[resource_key])
    return front


def _style_panel(ax, resource_label: str):
    """Shared axis text/tick styling of the plot family: bold axis labels (no
    per-panel title, the labels name the panel), inout ticks, major and minor
    grid."""
    ax.set_xlabel(resource_label, fontweight="bold")
    ax.set_ylabel("Latency (cycles)", fontweight="bold")
    ax.tick_params(which="both", length=4, width=1.0, direction="inout")
    # Major grid at the decades, a fainter minor grid at the 2..9 multiples.
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.35, alpha=0.35)


def make_plot_for_case(dir_case: Path, output_dir: Path):
    case_name = dir_case.name
    fp_all_eval_data_json = dir_case / "all_eval_data.json"
    eval_data = json.loads(fp_all_eval_data_json.read_text())

    n_rollouts = len(eval_data.keys())
    assert n_rollouts >= 1, f"Expected at least 1 rollout, but found {n_rollouts}"
    # only use the first one
    first_rollout_key = list(eval_data.keys())[0]
    sample_data = eval_data[first_rollout_key]

    iterations = sample_data.get("iterations", [])
    if not iterations:
        raise ValueError(f"No iterations recorded for case {case_name}.")

    # The baseline is only synthesized once per sample and reused across
    # iterations, so any iteration that ran evaluation carries the same value.
    baseline_point = next(
        (it["baseline"] for it in iterations if it.get("baseline") is not None), None
    )
    if baseline_point is None or not baseline_point["passed"]:
        raise ValueError(f"Baseline point did not pass for case {case_name}.")
    pareto_data_baseline = _extract_point(baseline_point)

    iteration_points: list[tuple[int, list[dict]]] = []
    for iteration in iterations:
        iter_index = iteration["iteration_index"]
        points = []
        for point in iteration.get("points", []):
            if not point["passed"] or not point["render_success"]:
                continue
            points.append(_extract_point(point))

        if any(point["latency"] is None for point in points):
            print(
                f"Skipping iteration {iter_index} for case {case_name} because "
                "one or more points have None latency."
            )
            continue
        if points:
            iteration_points.append((iter_index, points))

    if not iteration_points:
        print(f"Skipping case {case_name} because no iteration has usable points.")
        return

    # Color each iteration along a blue -> cyan -> green hue sweep (earliest ->
    # latest), and cycle marker shapes too, so nearby iterations stay easy to
    # tell apart; the baseline always stays red.
    n_iters = len(iteration_points)
    iter_colors = {
        iter_index: _iteration_color(0.0 if n_iters == 1 else i / (n_iters - 1))
        for i, (iter_index, _) in enumerate(iteration_points)
    }
    iter_markers = {
        iter_index: ITERATION_MARKERS[i % len(ITERATION_MARKERS)]
        for i, (iter_index, _) in enumerate(iteration_points)
    }

    legend_handles = [
        Line2D([0], [0], color="red", marker="o", linestyle="none", label="Baseline")
    ] + [
        Line2D(
            [0],
            [0],
            color=iter_colors[iter_index],
            marker=iter_markers[iter_index],
            linestyle="-",
            label=f"Iter {iter_index}",
        )
        for iter_index, _ in iteration_points
    ]

    apply_trj_style()
    fig, axes = plt.subplots(2, 2, figsize=(7, 5.6))
    for ax, (resource_key, (resource_label, total_key)) in zip(
        axes.flat, RESOURCE_TYPES.items()
    ):
        all_values = [pareto_data_baseline[resource_key]] + [
            point[resource_key]
            for _, points in iteration_points
            for point in points
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
            _style_panel(ax, resource_label)
            # Nothing to read off the placeholder axes, so no tick labels.
            ax.tick_params(labelbottom=False, labelleft=False)
            continue

        ax.scatter(
            [pareto_data_baseline[resource_key]],
            [pareto_data_baseline["latency"]],
            color="red",
            marker="o",
            s=22,
            zorder=5,
        )

        for iter_index, points in iteration_points:
            color = iter_colors[iter_index]
            ax.scatter(
                [point[resource_key] for point in points],
                [point["latency"] for point in points],
                color=color,
                marker=iter_markers[iter_index],
                s=22,
            )

            front = _pareto_front(points, resource_key)
            if not front:
                continue
            front_x = [point[resource_key] for point in front]
            front_y = [point["latency"] for point in front]
            if len(front) == 1:
                ax.plot(
                    front_x,
                    front_y,
                    color=color,
                    marker="o",
                    markersize=20,
                    markerfacecolor=color,
                    markeredgecolor=color,
                    alpha=0.3,
                    linestyle="none",
                    zorder=-5,
                )
            else:
                # No marker on the connecting line itself, so it doesn't paint
                # over the per-iteration marker shapes of the points it joins.
                ax.plot(
                    front_x,
                    front_y,
                    color=color,
                    linestyle="-",
                    linewidth=1.5,
                    zorder=-5,
                )

        total_resources = baseline_point["vitis_hls_tool_out"]["data_tool"][total_key]
        vline_transform = blended_transform_factory(ax.transData, ax.transAxes)
        for label_row, pct in enumerate([0.1, 0.25, 0.5, 0.75, 1.0]):
            vline_x = total_resources * pct
            ax.axvline(
                vline_x,
                color="gray",
                linestyle="--",
                linewidth=1.0,
                zorder=-10,
            )
            # Neighboring budget lines are close on the log axis, so alternate
            # the label height between two rows to keep the labels apart.
            label_y = LABEL_Y_ROWS[label_row % len(LABEL_Y_ROWS)]
            ax.text(
                vline_x,
                label_y,
                f"{int(pct * 100)}%",
                transform=vline_transform,
                fontsize=7,
                fontweight="bold",
                color="black",
                rotation=90,
                horizontalalignment="center",
                verticalalignment="center",
                bbox={
                    "boxstyle": "round,pad=0.15",
                    "facecolor": "white",
                    "edgecolor": "black",
                    "linewidth": 0.5,
                },
                zorder=-9,
            )
        ax.set_xscale("log")
        ax.set_yscale("log")
        _style_panel(ax, resource_label)

    pass_rate_parts = []
    for iteration in iterations:
        idx = iteration["iteration_index"]
        summary = iteration.get("summary")
        if summary is not None:
            pass_rate_parts.append(f"iter {idx}: {summary['n_passed']}/{summary['n_points']}")
        else:
            pass_rate_parts.append(f"iter {idx}: n/a")
    subtitle = "Pass rates: " + ", ".join(pass_rate_parts)

    # Title: "<design name>" from <source>. The design name is the benchmark
    # case's own name (no model suffix), the source its readable tag label.
    design_name = sample_data.get("benchmark_case_name") or case_name.rsplit("__", 1)[0]
    tags = sample_data.get("benchmark_case_tags") or []
    source = source_label(", ".join(sorted(tags))) if tags else "unknown source"
    title = f'"{design_name}" from {source}'
    fig.suptitle(title, y=0.995, fontweight="bold")
    fig.text(0.5, 0.945, subtitle, ha="center", va="top", fontsize=10)
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.915),
        ncol=len(legend_handles),
        prop={"size": 8.5, "weight": "bold"},
        frameon=False,
        columnspacing=1.0,
        handletextpad=0.4,
    )
    fig.tight_layout(rect=(0, 0, 1, 0.865))
    # tight_layout also reserves room for the figure-level legend, which leaves
    # a larger gap under it than between title, subtitle and legend; pin the top
    # of the axes so the four gaps are even.
    fig.subplots_adjust(top=AXES_TOP)

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)

    f_name = f"pareto_front_iterative__{case_name}.png"
    fp_fig = output_dir / f_name
    fig.savefig(fp_fig, bbox_inches="tight", pad_inches=0.02, dpi=300)

    plt.close(fig)


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

    if not DIR_FIGURES.exists():
        DIR_FIGURES.mkdir(parents=True, exist_ok=True)

    DIR_FIGURES_SINGLE = DIR_FIGURES / "single_agent_run_plots_iterative"

    def job(dir_case):
        print(f"Making plot for case {dir_case.name}...")
        make_plot_for_case(dir_case, DIR_FIGURES_SINGLE)
        return f"Done making plot for case {dir_case.name}"

    N_JOBS = 32

    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        futures = {
            executor.submit(job, dir_case): dir_case for dir_case in dir_cases_plot
        }
        for future in as_completed(futures):
            dir_case = futures[future]
            try:
                result = future.result()
                print(result)
            except Exception as e:
                print(f"Error making plot for case {dir_case.name}: {e}")
