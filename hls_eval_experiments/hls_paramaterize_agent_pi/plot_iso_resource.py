# given an eval dir witha bunch of run data ffor diffente deisgns, we want to make one bar chat sholwing the speedup of each case over teh baslein under differnt reousce cosatins,

# the idea is that for each percenmt of devie resouces (10%, 25%, 50%, 75%, 100%), we want to show the speedup of the best pareto optmial design that fits within all reouce constinat
# for example, for the 50% case, we compute what 50% is for each resource given the total reousrecs a device has, then we look at the pareto front and find the best design (least latency), where all the resource usage is less than or equal to 50% of the total device resources for all reouces types (you cannot have a design which is over the limit for one reousce type but not another)
# thne we want want to compute the the base_design_latecy / best_design_latency to get the speedup, and plot that as a bar chart for each case
# each tick on the x-ais is a different design, and we are doing a grouped bar plot for each desing and eahc goup in the cluster is each different resource constraint (10%, 25%, 50%, 75%, 100%)
# the y-axis is the speedup, and we want to have a horizontal line at y=1 to show the baseline, and any bar above that line is a speedup, and any bar below that line is a slowdown

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.transforms import blended_transform_factory

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data"

DIR_FIGURES = DIR_CURRENT / "figures"

# set matplotlib to use 'Agg' backend for headless environments
plt.switch_backend("Agg")

RESOURCE_KEYS = [
    ("resources_lut_used", "resources_lut_total"),
    ("resources_ff_used", "resources_ff_total"),
    ("resources_dsp_used", "resources_dsp_total"),
    ("resources_bram_used", "resources_bram_total"),
]

RESOURCE_BUDGET_PCTS = [0.10, 0.25, 0.50, 0.75, 1.00]


def _extract_point(point: dict) -> dict | None:
    data_tool = point.get("vitis_hls_tool_out", {}).get("data_tool") or {}
    latency = data_tool.get("latency_worst_cycles")
    used = {res_key: data_tool.get(res_key) for res_key, _ in RESOURCE_KEYS}
    totals = {tot_key: data_tool.get(tot_key) for _, tot_key in RESOURCE_KEYS}
    if latency is None or any(v is None for v in used.values()):
        return None
    if any(v is None for v in totals.values()):
        return None
    return {"latency": latency, **used, **totals}


def load_case_points(dir_case: Path) -> tuple[dict, list[dict]] | None:
    """Load the baseline and all passing, metric-eligible parameterized points.

    Returns (baseline_point, points) where points holds only the agent's
    parameterized design-space points, NOT the baseline. The baseline is the
    fixed speedup denominator; it is not itself a candidate for "best design
    under budget X" — that search is over the parameterized Pareto front only.
    """
    fp_all_eval_data_json = dir_case / "all_eval_data.json"
    if not fp_all_eval_data_json.exists():
        return None
    eval_data = json.loads(fp_all_eval_data_json.read_text())
    if not eval_data:
        return None
    first_rollout_key = list(eval_data.keys())[0]
    eval_data_first = eval_data[first_rollout_key]

    baseline_point = eval_data_first.get("baseline")
    if not baseline_point or not baseline_point.get("passed"):
        return None
    baseline = _extract_point(baseline_point)
    if baseline is None:
        return None

    points = []
    for point in eval_data_first.get("points", []):
        if not point.get("passed") or not point.get("render_success"):
            continue
        extracted = _extract_point(point)
        if extracted is None:
            continue
        points.append(extracted)

    return baseline, points


def get_case_tag(dir_case: Path) -> str:
    """Design-source grouping key, from the benchmark case's own tags."""
    fp_all_eval_data_json = dir_case / "all_eval_data.json"
    eval_data = json.loads(fp_all_eval_data_json.read_text())
    first_rollout_key = list(eval_data.keys())[0]
    tags = eval_data[first_rollout_key].get("benchmark_case_tags") or []
    return ", ".join(sorted(tags)) if tags else "(untagged)"


def best_latency_within_budget(
    points: list[dict], pct: float, totals: dict[str, float]
) -> float | None:
    """Least latency among points whose usage is <= pct of every resource total.

    A point that exceeds the budget on even one resource type is infeasible,
    regardless of how far under budget it is on the others.
    """
    feasible = [
        point
        for point in points
        if all(
            point[res_key] <= pct * totals[tot_key]
            for res_key, tot_key in RESOURCE_KEYS
        )
    ]
    if not feasible:
        return None
    return min(point["latency"] for point in feasible)


def compute_case_speedups(dir_case: Path) -> dict[float, float | None] | None:
    loaded = load_case_points(dir_case)
    if loaded is None:
        return None
    baseline, points = loaded
    totals = {tot_key: baseline[tot_key] for _, tot_key in RESOURCE_KEYS}
    if any(not total or total <= 0 for total in totals.values()):
        return None
    if not baseline["latency"] or baseline["latency"] <= 0:
        return None

    speedups: dict[float, float | None] = {}
    for pct in RESOURCE_BUDGET_PCTS:
        best_latency = best_latency_within_budget(points, pct, totals)
        speedups[pct] = (
            baseline["latency"] / best_latency
            if best_latency is not None and best_latency > 0
            else None
        )
    return speedups


def make_iso_resource_plot(
    dir_cases: list[Path],
    output_dir: Path,
    fig_name: str = "iso_resource_speedup.png",
) -> None:
    case_speedups: dict[str, dict[float, float | None]] = {}
    case_tags: dict[str, str] = {}
    for dir_case in sorted(dir_cases, key=lambda d: d.name):
        speedups = compute_case_speedups(dir_case)
        if speedups is None:
            print(f"Skipping case {dir_case.name}: no usable baseline/points.")
            continue
        case_speedups[dir_case.name] = speedups
        case_tags[dir_case.name] = get_case_tag(dir_case)

    if not case_speedups:
        print("No cases with usable data; nothing to plot.")
        return

    # Group by design source (tag) first, then within each group sort from
    # lowest to best speedup under the most generous resource budget.
    most_generous_pct = max(RESOURCE_BUDGET_PCTS)

    def sort_key(name: str) -> tuple[str, float]:
        speedup = case_speedups[name].get(most_generous_pct)
        return (case_tags[name], speedup if speedup is not None else float("-inf"))

    case_names = sorted(case_speedups.keys(), key=sort_key)
    n_cases = len(case_names)
    n_groups = len(RESOURCE_BUDGET_PCTS)

    # Display-only: every case name is "<design_name>__<model_name>", and the
    # trailing model segment is identical across the whole run, so drop it
    # from the tick labels rather than the internal keys.
    model_suffixes = {name.rsplit("__", 1)[-1] for name in case_names if "__" in name}
    if len(model_suffixes) == 1:
        display_names = [name.rsplit("__", 1)[0] for name in case_names]
    else:
        display_names = case_names

    x = np.arange(n_cases)
    width = 0.8 / n_groups
    colors = plt.cm.viridis(np.linspace(0, 1, n_groups))

    fig, ax = plt.subplots(figsize=(14, 5))

    # x in data coords, y pinned to a fixed fraction of the axes height, so
    # both the group boundaries/labels and the infeasibility markers stay put
    # regardless of the (log-scaled) y-range.
    axes_trans = blended_transform_factory(ax.transData, ax.transAxes)
    infeasible_trans = axes_trans
    infeasible_marker_y = 0.015

    # Group boundaries (contiguous runs of the same tag after sorting above).
    group_bounds: list[tuple[str, int, int]] = []
    group_start = 0
    for i in range(1, n_cases + 1):
        if (
            i == n_cases
            or case_tags[case_names[i]] != case_tags[case_names[group_start]]
        ):
            group_bounds.append((case_tags[case_names[group_start]], group_start, i))
            group_start = i

    # Mark the boundaries between design-source (tag) groups, and label each
    # group with its tag centered above that region.
    for tag, start, end in group_bounds:
        if start > 0:
            ax.axvline(
                start - 0.5, color="gray", linestyle="-", linewidth=0.8, zorder=-8
            )
        ax.text(
            (start + end - 1) / 2,
            0.97,
            tag,
            transform=axes_trans,
            ha="center",
            va="top",
            fontsize=9,
            fontweight="bold",
            bbox={
                "boxstyle": "round,pad=0.3",
                "facecolor": "white",
                "edgecolor": "black",
                "linewidth": 0.8,
            },
            zorder=6,
        )

    for i, pct in enumerate(RESOURCE_BUDGET_PCTS):
        heights = [case_speedups[name][pct] for name in case_names]
        heights = [h if h is not None else np.nan for h in heights]
        offset = (i - (n_groups - 1) / 2) * width
        bar_positions = x + offset
        ax.bar(
            bar_positions,
            heights,
            width=width,
            label=f"{int(pct * 100)}% of device",
            color=colors[i],
        )

        infeasible_positions = [
            pos for pos, h in zip(bar_positions, heights) if np.isnan(h)
        ]
        if infeasible_positions:
            ax.plot(
                infeasible_positions,
                [infeasible_marker_y] * len(infeasible_positions),
                marker="x",
                color="red",
                linestyle="none",
                markersize=5,
                markeredgewidth=1.5,
                transform=infeasible_trans,
                zorder=5,
            )

    # single legend entry representing all the red-x markers above
    ax.plot(
        [],
        [],
        marker="x",
        color="red",
        linestyle="none",
        markersize=5,
        markeredgewidth=1.5,
        label="No feasible design",
    )

    ax.axhline(1.0, color="black", linestyle="--", linewidth=1, zorder=-1)
    ax.set_yscale("log")
    ax.set_axisbelow(True)
    ax.grid(True, which="major", axis="y", color="lightgrey", linewidth=0.7, zorder=0)
    ax.grid(True, which="minor", axis="y", color="lightgrey", linewidth=0.35, zorder=0)
    ax.set_xlim(-0.5, n_cases - 0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(display_names, rotation=30, ha="right", fontsize=8)
    ax.set_ylabel("Speedup over baseline\n(baseline latency / best feasible latency)")
    ax.set_xlabel("Design case")
    ax.set_title("Best Speedup Under Iso-Resource Budgets", pad=48)
    ax.legend(
        title="Resource budget",
        fontsize=8,
        ncol=len(RESOURCE_BUDGET_PCTS) + 1,
        loc="lower center",
        bbox_to_anchor=(0.5, 1.0),
    )
    fig.tight_layout()

    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / fig_name, dpi=300)
    plt.close(fig)


if __name__ == "__main__":
    dir_cases_plot = []

    all_dir_cases = list(DIR_OUTPUT_DATA.iterdir())
    for dir_case in all_dir_cases:
        if not dir_case.is_dir():
            continue

        fp_all_eval_data_json = dir_case / "all_eval_data.json"
        if not fp_all_eval_data_json.exists():
            print(
                f"Skipping {dir_case} because it does not have an all_eval_data.json file."
            )
            continue

        dir_cases_plot.append(dir_case)

    make_iso_resource_plot(dir_cases_plot, DIR_FIGURES)
