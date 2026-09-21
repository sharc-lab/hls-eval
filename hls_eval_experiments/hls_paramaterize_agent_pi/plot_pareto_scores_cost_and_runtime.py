import json
import math
from datetime import datetime
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from plot_style_trj import (
    GREY,
    GREY_ALPHA,
    GREY_LW,
    MEAN_LW,
    finish_figure,
    new_stacked_figure,
    source_color_map,
    source_label,
    style_score_row,
)

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data_v2_big_run"

DIR_FIGURES = DIR_CURRENT / "figures"

# set matplotlib to use 'Agg' backend for headless environments
plt.switch_backend("Agg")

# Additive margin in log10 space, equal to a 1.1x margin on the raw values.
REFERENCE_MARGIN_LOG = math.log10(1.1)

# (label, key in data_tool, line color)
RESOURCE_TYPES = {
    "resources_lut_used": ("LUTs", "tab:blue"),
    "resources_ff_used": ("FFs", "tab:orange"),
    "resources_dsp_used": ("DSPs", "tab:green"),
    "resources_bram_used": ("BRAMs", "tab:red"),
}


def _is_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _extract_point(point: dict) -> dict | None:
    """Latency/resource values for a scoreable point, else None (matching the
    evaluator, a point without every metric cannot enter a Pareto front)."""
    if not point.get("passed") or not point.get("render_success"):
        return None
    metrics = point["vitis_hls_tool_out"]["data_tool"] or {}
    values = {"latency": metrics.get("latency_worst_cycles")}
    values.update({key: metrics.get(key) for key in RESOURCE_TYPES})
    if not all(_is_number(value) for value in values.values()):
        return None
    return values


def _to_log(points: list[dict], resource_key: str) -> list[dict]:
    return [
        {
            resource_key: math.log10(p[resource_key] + 1),
            "latency": math.log10(p["latency"] + 1),
        }
        for p in points
    ]


def _pareto_front(points: list[dict], resource_key: str) -> list[dict]:
    """Nondominated points in (resource, latency); both are minimized."""
    return [
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


def _hypervolume(
    points: list[dict], resource_key: str, ref_resource: float, ref_latency: float
) -> float:
    """2D dominated area between the points and the reference point."""
    volume = 0.0
    prev_latency = ref_latency
    for point in sorted(points, key=lambda p: (p[resource_key], p["latency"])):
        # Points at or beyond the reference point add no area (and would add
        # negative area if not skipped).
        if point[resource_key] >= ref_resource or point["latency"] >= prev_latency:
            continue
        volume += (ref_resource - point[resource_key]) * (
            prev_latency - point["latency"]
        )
        prev_latency = point["latency"]
    return volume


class CaseScores(NamedTuple):
    iter_indices: list[int]
    scores_by_resource: dict[str, list[float]]
    covers_by_resource: dict[str, list[bool]]
    # Cumulative agent cost ($) / time (s) through the end of each iteration
    cumulative_cost: list[float]
    cumulative_seconds: list[float]
    # Benchmark source of the design, e.g. rodinia_clean or athena_crypto
    source: str


def _agent_cost_and_seconds(agent_trace: list[dict]) -> tuple[float, float]:
    """Cost ($) and duration (s) of one agent session, from its trace: the sum
    of the per-response costs, and the span between the session's first and last
    entries. Verification runs (csim/csynth by the evaluator) happen outside the
    session and are not counted."""
    cost = sum(
        ((entry["message"].get("usage") or {}).get("cost") or {}).get("total", 0.0)
        for entry in agent_trace
        if entry.get("type") == "message" and entry["message"].get("role") == "assistant"
    )
    timestamps = [
        datetime.fromisoformat(entry["timestamp"].replace("Z", "+00:00"))
        for entry in agent_trace
        if entry.get("timestamp")
    ]
    seconds = (max(timestamps) - min(timestamps)).total_seconds() if timestamps else 0.0
    return cost, seconds


class CaseData(NamedTuple):
    case_name: str
    iter_indices: list[int]
    # Scoreable (passed, fully measured) points of each iteration
    iter_points: list[list[dict]]
    # The untouched baseline design's metrics, or None if unusable
    baseline: dict | None
    cumulative_cost: list[float]
    cumulative_seconds: list[float]
    source: str


def _load_case_data(dir_case: Path) -> CaseData:
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

    iter_indices = [iteration["iteration_index"] for iteration in iterations]
    iter_points = [
        [
            extracted
            for point in iteration.get("points", [])
            if (extracted := _extract_point(point)) is not None
        ]
        for iteration in iterations
    ]

    cumulative_cost: list[float] = []
    cumulative_seconds: list[float] = []
    total_cost = total_seconds = 0.0
    for iteration in iterations:
        cost, seconds = _agent_cost_and_seconds(iteration.get("agent_trace") or [])
        total_cost += cost
        total_seconds += seconds
        cumulative_cost.append(total_cost)
        cumulative_seconds.append(total_seconds)

    # The baseline is evaluated once per sample and repeated in every iteration
    # that ran evaluation; it has no render_success, being the untouched design.
    baseline_raw = next(
        (it["baseline"] for it in iterations if it.get("baseline") is not None), None
    )
    baseline = (
        _extract_point({**baseline_raw, "render_success": True})
        if baseline_raw is not None
        else None
    )
    if baseline is None:
        print(
            f"WARNING: {case_name}: no usable baseline; scores are NOT "
            "baseline-anchored (0 does not mean 'no better than the baseline')."
        )

    return CaseData(
        case_name,
        iter_indices,
        iter_points,
        baseline,
        cumulative_cost,
        cumulative_seconds,
        "/".join(sample_data.get("benchmark_case_tags") or ["unknown"]),
    )


def _compute_case_scores(
    dir_case: Path,
) -> CaseScores:
    """Scores how well the Pareto front improves (or not) over agent iterations,
    anchored to the baseline so that 0 means "no better than the baseline".

    For each resource type, the parameterized points of each iteration give a
    Pareto front P_i in (resource, latency), with both axes in log10(x + 1)
    space. The baseline B is not part of any P_i, but it is added to the
    combined front P* and to every iteration's hypervolume. The reference point
    is the max latency and max resource of P* (with B), plus log10(1.1). Each
    iteration is scored as (H(P_i + B) - H(B)) / (H(P* + B) - H(B)), which is in
    [0, 1]. An iteration with no scoreable points has an empty front, scored
    NaN. If the baseline is unusable, scores fall back to the unanchored
    H(P_i) / H(P*), with a warning.

    Returns the iteration indices and, per scoreable resource type, one score
    per iteration, plus per resource type whether each iteration's front
    contains a point at least as good as the baseline in both latency and that
    resource. Resource types with nothing to score are left out. Also returns
    the cumulative agent cost and time through each iteration, so an
    iteration's design is charged for every agent run that produced it.
    """
    (
        case_name,
        iter_indices,
        iter_points,
        baseline,
        cumulative_cost,
        cumulative_seconds,
        source,
    ) = _load_case_data(dir_case)

    scores_by_resource: dict[str, list[float]] = {}
    covers_by_resource: dict[str, list[bool]] = {}
    for resource_key in RESOURCE_TYPES:
        # Fronts, reference point and hypervolumes are all computed in
        # log10(x + 1) space, so scores aren't dominated by the largest values.
        fronts = [
            _pareto_front(_to_log(points, resource_key), resource_key)
            for points in iter_points
        ]
        baseline_points = _to_log([baseline], resource_key) if baseline else []
        all_front_points = [point for front in fronts for point in front]
        if not all_front_points:
            continue
        if all(point[resource_key] == 0 for point in all_front_points + baseline_points):
            # e.g. a design that never uses DSPs: nothing to score
            continue

        # The reference point comes from the combined front P* (with the
        # baseline), not from every iteration's front, so dominated early
        # points don't stretch the box.
        combined_front = _pareto_front(all_front_points + baseline_points, resource_key)
        ref_latency = REFERENCE_MARGIN_LOG + max(p["latency"] for p in combined_front)
        ref_resource = REFERENCE_MARGIN_LOG + max(
            p[resource_key] for p in combined_front
        )

        def hv(points: list[dict]) -> float:
            return _hypervolume(points, resource_key, ref_resource, ref_latency)

        hv_base = hv(baseline_points)
        denominator = hv(combined_front) - hv_base
        if denominator <= 0:
            print(
                f"{case_name}: no point beats the baseline on latency vs. "
                f"{RESOURCE_TYPES[resource_key][0]}; skipping that score."
            )
            continue

        scores_by_resource[resource_key] = [
            (hv(front + baseline_points) - hv_base) / denominator if front else math.nan
            for front in fronts
        ]
        if baseline_points:
            covers_by_resource[resource_key] = [
                any(
                    p[resource_key] <= baseline_points[0][resource_key]
                    and p["latency"] <= baseline_points[0]["latency"]
                    for p in front
                )
                for front in fronts
            ]
    return CaseScores(
        iter_indices,
        scores_by_resource,
        covers_by_resource,
        cumulative_cost,
        cumulative_seconds,
        source,
    )


def _plot_score_line(
    ax,
    iter_indices: list[int],
    scores: list[float],
    color,
    label: str | None,
    gap_label: str | None = None,
    **line_kwargs,
) -> bool:
    """Plots one score line; NaN scores break it, and each break is bridged
    with a thin gray dotted line. Returns whether a gap bridge was drawn."""
    ax.plot(iter_indices, scores, color=color, marker="o", label=label, **line_kwargs)
    scored = [
        (pos, score) for pos, score in enumerate(scores) if not math.isnan(score)
    ]
    drew_gap = False
    for (pos0, score0), (pos1, score1) in zip(scored, scored[1:]):
        if pos1 - pos0 > 1:
            ax.plot(
                [iter_indices[pos0], iter_indices[pos1]],
                [score0, score1],
                color="gray",
                linestyle=":",
                linewidth=GREY_LW,
                label=gap_label if not drew_gap else None,
                zorder=0,
            )
            drew_gap = True
    return drew_gap


def make_combined_plot(
    case_scores: dict[str, CaseScores],
    output_dir: Path,
    x_attr: str,
    x_label: str,
    filename: str,
):
    """One row per resource type: every design's score line in faint gray
    against cumulative agent cost or time, plus, per benchmark source, one
    colored line joining the mean x and mean score of that source's designs at
    each iteration."""
    case_names = sorted(case_scores)
    sources = sorted({case.source for case in case_scores.values()})
    source_colors = source_color_map(sources)
    max_x = max(getattr(case, x_attr)[-1] for case in case_scores.values())

    fig, axes = new_stacked_figure(
        len(RESOURCE_TYPES),
        f"Pareto Front Hypervolume Ratio vs. {x_label.split(' (')[0].title()}",
        f"{len(case_names)} designs | mean per benchmark source",
    )
    sources_present: set[str] = set()
    for ax, (resource_key, (resource_label, _)) in zip(axes, RESOURCE_TYPES.items()):
        # source -> iteration index -> (x, score) of each of its designs there
        points_by_source: dict[str, dict[int, list[tuple[float, float]]]] = {}
        designs_per_source: dict[str, int] = {}
        for name in case_names:
            case = case_scores[name]
            if resource_key not in case.scores_by_resource:
                continue
            x_values = getattr(case, x_attr)
            scores = case.scores_by_resource[resource_key]
            _plot_score_line(
                ax,
                x_values,
                scores,
                GREY,
                None,
                linewidth=GREY_LW,
                markersize=0,
                alpha=GREY_ALPHA,
                zorder=2,
            )
            source_points = points_by_source.setdefault(case.source, {})
            for iter_index, x, score in zip(case.iter_indices, x_values, scores):
                if not math.isnan(score):
                    source_points.setdefault(iter_index, []).append((x, score))
            designs_per_source[case.source] = designs_per_source.get(case.source, 0) + 1

        n_lines = sum(designs_per_source.values())
        if n_lines == 0:
            ax.text(
                0.5,
                0.5,
                f"No design uses {resource_label}",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
        # One mean line per source: at each iteration, the mean x and mean score
        # of that source's designs that have a score there.
        for source, points_at_iter in points_by_source.items():
            mean_iters = sorted(points_at_iter)
            color = source_colors[source]
            ax.plot(
                [sum(x for x, _ in points_at_iter[i]) / len(points_at_iter[i]) for i in mean_iters],
                [sum(y for _, y in points_at_iter[i]) / len(points_at_iter[i]) for i in mean_iters],
                color=color,
                lw=MEAN_LW,
                zorder=4,
                marker="o",
                markersize=5,
                markerfacecolor="white",
                markeredgecolor=color,
                markeredgewidth=1,
            )
            sources_present.add(source)
        style_score_row(
            ax,
            f"vs. {resource_label}",
            f"Latency vs. {resource_label} ({n_lines})",
            (0, max_x * 1.02),
            ax is axes[-1],
            box_edge_color="tab:blue",
        )

    finish_figure(
        fig,
        output_dir / filename,
        [
            Line2D([0], [0], color=GREY, alpha=0.8, label="Individual design"),
            *[
                Line2D(
                    [0],
                    [0],
                    color=source_colors[source],
                    lw=MEAN_LW,
                    marker="o",
                    markersize=5,
                    markerfacecolor="white",
                    markeredgecolor=source_colors[source],
                    label=f"Mean, {source_label(source)}",
                )
                for source in sources
                if source in sources_present
            ],
            Line2D(
                [0],
                [0],
                color="gray",
                linestyle=":",
                linewidth=GREY_LW,
                label="Gap (no scoreable points)",
            ),
        ],
        x_label.title(),
    )


if __name__ == "__main__":
    dir_cases_plot = []

    for dir_case in DIR_OUTPUT_DATA.iterdir():
        if not dir_case.is_dir():
            continue

        if not (dir_case / "all_eval_data.json").exists():
            print(
                f"Skipping {dir_case} because it does not have an all_eval_data.json file."
            )
            continue

        dir_cases_plot.append(dir_case)

    DIR_FIGURES_SCORES = DIR_FIGURES / "pareto_score_cost_and_runtime_plots"

    N_JOBS = 32

    case_scores: dict[str, CaseScores] = {}
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        futures = {
            executor.submit(_compute_case_scores, dir_case): dir_case
            for dir_case in dir_cases_plot
        }
        for future in as_completed(futures):
            dir_case = futures[future]
            try:
                result = future.result()
                if result.scores_by_resource:
                    case_scores[dir_case.name] = result
                else:
                    print(f"Skipping case {dir_case.name}: no scoreable points.")
            except Exception as e:
                print(f"Error scoring case {dir_case.name}: {e}")

    make_combined_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_cost",
        "Cumulative agent cost ($)",
        "pareto_score__all_designs__cost.png",
    )
    make_combined_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_seconds",
        "Cumulative agent time (s)",
        "pareto_score__all_designs__runtime.png",
    )
    print(f"Done making cost and runtime plots for {len(case_scores)} designs")
