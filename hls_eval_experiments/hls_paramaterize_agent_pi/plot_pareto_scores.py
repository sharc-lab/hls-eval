import json
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D

from plot_style_trj import (
    GREY,
    GREY_ALPHA,
    GREY_LW,
    MEAN_LW,
    finish_figure,
    source_color_map,
    new_stacked_figure,
    set_two_line_score_ylabel,
    source_label,
    style_score_row,
)

DIR_CURRENT = Path(__file__).parent

DIR_OUTPUT_DATA = DIR_CURRENT / "output_data_v2_big_run"

DIR_FIGURES = DIR_CURRENT / "figures"

# set matplotlib to use 'Agg' backend for headless environments
plt.switch_backend("Agg")

# Additive margin in log10 space, equal to a 1.1x margin on the raw values.
AVERAGE_LINE_COLOR = "tab:blue"

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


def _compute_case_scores(
    dir_case: Path,
) -> tuple[list[int], dict[str, list[float]], dict[str, list[bool]]]:
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
    resource. Resource types with nothing to score are left out.
    """
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
    return iter_indices, scores_by_resource, covers_by_resource


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
    with a gray dotted line. Returns whether a gap bridge was drawn."""
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


def make_plot_for_case(dir_case: Path, output_dir: Path):
    case_name = dir_case.name
    iter_indices, scores_by_resource, covers_by_resource = _compute_case_scores(
        dir_case
    )

    if not scores_by_resource:
        print(f"Skipping case {case_name} because no iteration has scoreable points.")
        return None

    fig, ax = plt.subplots(figsize=(8, 6))
    gap_labeled = False
    regression_labeled = False
    for resource_key, scores in scores_by_resource.items():
        resource_label, color = RESOURCE_TYPES[resource_key]
        drew_gap = _plot_score_line(
            ax,
            iter_indices,
            scores,
            color,
            resource_label,
            gap_label=None if gap_labeled else "Gap (no scoreable points)",
        )
        gap_labeled = gap_labeled or drew_gap
        # Mark iterations whose front has no point at least as good as the
        # baseline in both latency and this resource (a regression).
        regressions = [
            (x, score)
            for x, score, covers in zip(
                iter_indices, scores, covers_by_resource.get(resource_key, [])
            )
            if not covers and not math.isnan(score)
        ]
        if regressions:
            ax.plot(
                *zip(*regressions),
                linestyle="none",
                marker="x",
                color="red",
                markersize=12,
                markeredgewidth=2,
                zorder=6,
                label=None if regression_labeled else "Front doesn't cover baseline",
            )
            regression_labeled = True

    ax.set_xticks(iter_indices)
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("Iteration")
    ax.set_ylabel("Baseline-anchored hypervolume ratio")
    ax.set_title(f"{case_name}\nPareto front hypervolume ratio per iteration")
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(title="Latency vs.", fontsize=8)
    fig.tight_layout()

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_dir / f"pareto_score__{case_name}.png", dpi=300)
    plt.close(fig)
    return iter_indices, scores_by_resource


def _case_source(dir_case: Path) -> str:
    """Benchmark source of a design (its `benchmark_case_tags`), e.g. rodinia_clean."""
    eval_data = json.loads((dir_case / "all_eval_data.json").read_text())
    tags = eval_data[list(eval_data.keys())[0]].get("benchmark_case_tags") or []
    return "/".join(tags) if tags else "unknown"


def make_combined_plot(
    case_scores: dict[str, tuple[list[int], dict[str, list[float]]]],
    case_sources: dict[str, str],
    output_dir: Path,
    by_source: bool = False,
    filename: str = "pareto_score__all_designs.png",
):
    """One row per resource type: every design's score line in faint gray, plus
    the mean score across designs at each iteration: one blue line over all
    designs, or (by_source) one colored line per benchmark source."""
    case_names = sorted(case_scores)
    sources = sorted(set(case_sources.values()))
    source_colors = source_color_map(sources)
    max_iter = max(
        (max(iter_indices) for iter_indices, _ in case_scores.values()), default=0
    )

    fig, axes = new_stacked_figure(
        len(RESOURCE_TYPES),
        "Parameterized Design Pareto Frontier Scores per Iteration",
        # The by-source plot names the sources in its legend instead.
        ""
        if by_source
        else f"{len(case_names)} designs across "
        + ", ".join(source_label(s) for s in sorted(set(case_sources.values()))),
    )
    for ax, (resource_key, (resource_label, _)) in zip(axes, RESOURCE_TYPES.items()):
        # group -> iteration index -> scores of every design that has one there;
        # the group is the benchmark source, or "" for a single mean over all
        scores_at_iter: dict[str, dict[int, list[float]]] = {}
        n_lines = 0
        for name in case_names:
            iter_indices, scores_by_resource = case_scores[name]
            if resource_key not in scores_by_resource:
                continue
            scores = scores_by_resource[resource_key]
            _plot_score_line(
                ax,
                iter_indices,
                scores,
                GREY,
                None,
                linewidth=GREY_LW,
                markersize=0,
                alpha=GREY_ALPHA,
                zorder=2,
            )
            group = case_sources[name] if by_source else ""
            for iter_index, score in zip(iter_indices, scores):
                if not math.isnan(score):
                    scores_at_iter.setdefault(group, {}).setdefault(
                        iter_index, []
                    ).append(score)
            n_lines += 1

        if n_lines == 0:
            ax.text(
                0.5,
                0.5,
                f"No design uses {resource_label}",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
        else:
            for group, group_scores_at_iter in scores_at_iter.items():
                line_color = source_colors[group] if by_source else AVERAGE_LINE_COLOR
                mean_iters = sorted(group_scores_at_iter)
                ax.plot(
                    mean_iters,
                    [
                        sum(group_scores_at_iter[i]) / len(group_scores_at_iter[i])
                        for i in mean_iters
                    ],
                    color=line_color,
                    lw=MEAN_LW,
                    zorder=4,
                    marker="o",
                    markersize=5,
                    markerfacecolor="white",
                    markeredgecolor=line_color,
                    markeredgewidth=1,
                )
        ax.set_xticks(range(max_iter + 1))
        style_score_row(
            ax,
            f"vs. {resource_label}",
            None,  # no boxed label: the y label already names the resource
            (0, max_iter),
            ax is axes[-1],
            box_edge_color="black",
            y_limits=(0.0, 1.0),
        )
        set_two_line_score_ylabel(ax, resource_label)

    finish_figure(
        fig,
        output_dir / filename,
        [
            Line2D([0], [0], color=GREY, alpha=0.8, label="Individual design"),
            *[
                Line2D(
                    [0],
                    [0],
                    color=color,
                    lw=MEAN_LW,
                    marker="o",
                    markersize=5,
                    markerfacecolor="white",
                    markeredgecolor=color,
                    label=label,
                )
                for color, label in (
                    [(source_colors[src], f"Mean, {source_label(src)}") for src in sources]
                    if by_source
                    else [(AVERAGE_LINE_COLOR, "Average")]
                )
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
        "Agent Iteration Step",
        legend_fontsize=10,
        legend_bold=True,
        legend_y=0.955 if by_source else 0.925,
        rect_top=0.945 if by_source else 0.94,
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

    DIR_FIGURES_SCORES = DIR_FIGURES / "pareto_score_plots"
    DIR_FIGURES_SCORES.mkdir(parents=True, exist_ok=True)

    def job(dir_case):
        print(f"Making plot for case {dir_case.name}...")
        return make_plot_for_case(dir_case, DIR_FIGURES_SCORES)

    N_JOBS = 32

    case_scores: dict[str, tuple[list[int], dict[str, list[float]]]] = {}
    with ProcessPoolExecutor(max_workers=N_JOBS) as executor:
        futures = {
            executor.submit(job, dir_case): dir_case for dir_case in dir_cases_plot
        }
        for future in as_completed(futures):
            dir_case = futures[future]
            try:
                result = future.result()
                if result is not None:
                    case_scores[dir_case.name] = result
                print(f"Done making plot for case {dir_case.name}")
            except Exception as e:
                print(f"Error making plot for case {dir_case.name}: {e}")

    case_sources = {name: _case_source(DIR_OUTPUT_DATA / name) for name in case_scores}
    make_combined_plot(case_scores, case_sources, DIR_FIGURES_SCORES)
    make_combined_plot(
        case_scores,
        case_sources,
        DIR_FIGURES_SCORES,
        by_source=True,
        filename="pareto_score__all_designs__by_source.png",
    )
    print(f"Done making combined plot for {len(case_scores)} designs")
