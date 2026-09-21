"""Iso-cost / iso-runtime Pareto hypervolume scores.

For a budget B (cumulative agent cost in $, or cumulative agent time in s), take
every scoreable design point from all iterations whose cumulative spend fits
within B, build one Pareto front from that pool, and score it with the same
baseline-anchored, log-space hypervolume ratio as plot_pareto_scores.py. Unlike
the per-iteration scores, the pool is cumulative, so each design's curve never
decreases, and it reaches 1 once the design's whole run fits in the budget.
"""

import bisect
import math
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path
from typing import NamedTuple

import numpy as np
from matplotlib.lines import Line2D

from plot_pareto_scores_cost_and_runtime import (
    DIR_FIGURES,
    DIR_OUTPUT_DATA,
    REFERENCE_MARGIN_LOG,
    RESOURCE_TYPES,
    _hypervolume,
    _load_case_data,
    _pareto_front,
    _to_log,
)
from plot_style_trj import (
    GREY,
    GREY_ALPHA,
    GREY_LW,
    MEAN_LW,
    finish_figure,
    new_stacked_figure,
    set_two_line_score_ylabel,
    source_color_map,
    source_label,
    style_score_row,
)

N_BUDGET_POINTS = 400

# Whether the plots carry the "<n> designs across ... | <what> within the <x> budget"
# subtitle under the title.
SHOW_SUBTITLE = False


class IsoBudgetScores(NamedTuple):
    source: str
    cumulative_cost: list[float]
    cumulative_seconds: list[float]
    # Per scoreable resource type: score of the pool of all points from
    # iterations 0..i, for each iteration i (NaN while that pool is empty)
    pool_scores_by_resource: dict[str, list[float]]
    # Per scoreable resource type: score of iteration i's OWN front alone (no
    # points carried over from earlier iterations), for each iteration i. An
    # iteration with no scoreable points holds the previous iteration's score
    # (NaN if there is none yet).
    iter_scores_by_resource: dict[str, list[float]]


def _compute_pool_scores(dir_case: Path) -> IsoBudgetScores:
    data = _load_case_data(dir_case)

    pool_scores_by_resource: dict[str, list[float]] = {}
    iter_scores_by_resource: dict[str, list[float]] = {}
    for resource_key in RESOURCE_TYPES:
        # Same as the per-iteration scores: everything in log10(x + 1) space,
        # the reference point and denominator from the combined front P* (which
        # includes the baseline), and scores anchored to the baseline.
        iter_points = [_to_log(points, resource_key) for points in data.iter_points]
        baseline_points = _to_log([data.baseline], resource_key) if data.baseline else []
        all_points = [point for points in iter_points for point in points]
        if not all_points:
            continue
        if all(point[resource_key] == 0 for point in all_points + baseline_points):
            # e.g. a design that never uses DSPs: nothing to score
            continue

        combined_front = _pareto_front(all_points + baseline_points, resource_key)
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
                f"{data.case_name}: no point beats the baseline on latency vs. "
                f"{RESOURCE_TYPES[resource_key][0]}; skipping that score."
            )
            continue

        pool: list[dict] = []
        scores = []
        for points in iter_points:
            pool = pool + points
            scores.append(
                (hv(_pareto_front(pool, resource_key) + baseline_points) - hv_base)
                / denominator
                if pool
                else math.nan
            )
        pool_scores_by_resource[resource_key] = scores

        # Alternative scoring: each iteration's own front, not the running pool.
        iter_scores: list[float] = []
        for points in iter_points:
            if points:
                iter_scores.append(
                    (hv(_pareto_front(points, resource_key) + baseline_points) - hv_base)
                    / denominator
                )
            else:
                iter_scores.append(iter_scores[-1] if iter_scores else math.nan)
        iter_scores_by_resource[resource_key] = iter_scores

    return IsoBudgetScores(
        data.source,
        data.cumulative_cost,
        data.cumulative_seconds,
        pool_scores_by_resource,
        iter_scores_by_resource,
    )


def _score_at_budgets(
    cumulative_spend: list[float], pool_scores: list[float], budgets: np.ndarray
) -> np.ndarray:
    """Step function: the score of the pool of iterations that fit in each budget
    (NaN before the first iteration fits, and held flat after the last one)."""
    scores = np.full(len(budgets), np.nan)
    for i, budget in enumerate(budgets):
        last_fit = bisect.bisect_right(cumulative_spend, budget) - 1
        if last_fit >= 0:
            scores[i] = pool_scores[last_fit]
    return scores


def make_iso_budget_plot(
    case_scores: dict[str, IsoBudgetScores],
    output_dir: Path,
    x_attr: str,
    x_label: str,
    filename: str,
    budget_name: str,
    score_attr: str = "pool_scores_by_resource",
    score_description: str = "all points",
    title: str = "Pareto Front Hypervolume Ratio Within a Budget",
    two_line_ylabel: bool = False,
    show_row_box: bool = True,
    y_limits: tuple[float, float] = (-0.04, 1.04),
):
    """One row per resource type: every design's score-vs-budget curve in faint
    gray, plus one colored mean curve per benchmark source.

    score_attr picks the scoring approach: "pool_scores_by_resource" (front of
    all points from the iterations that fit in the budget) or
    "iter_scores_by_resource" (front of the latest completed iteration alone).
    score_description is the phrase for it in the subtitle. two_line_ylabel uses
    the bold "Pareto Score" / "(Lat. vs. <resource>)" y label of the score plots;
    show_row_box toggles the boxed "Latency vs. <resource> (n)" label at the
    bottom right of each row."""
    case_names = sorted(case_scores)
    sources = sorted({case.source for case in case_scores.values()})
    source_colors = source_color_map(sources)
    max_budget = max(getattr(case, x_attr)[-1] for case in case_scores.values())
    budgets = np.linspace(0, max_budget, N_BUDGET_POINTS)

    fig, axes = new_stacked_figure(
        len(RESOURCE_TYPES),
        title,
        (
            f"{len(case_names)} designs across "
            + ", ".join(source_label(s) for s in sources)
            + f" | {score_description} within the {budget_name} budget"
            if SHOW_SUBTITLE
            else ""
        ),
    )
    sources_present: set[str] = set()
    for ax, (resource_key, (resource_label, _)) in zip(axes, RESOURCE_TYPES.items()):
        curves_by_source: dict[str, list[np.ndarray]] = {}
        for name in case_names:
            case = case_scores[name]
            case_resource_scores = getattr(case, score_attr)
            if resource_key not in case_resource_scores:
                continue
            curve = _score_at_budgets(
                getattr(case, x_attr), case_resource_scores[resource_key], budgets
            )
            ax.plot(
                budgets, curve, color=GREY, linewidth=GREY_LW, alpha=GREY_ALPHA, zorder=2
            )
            curves_by_source.setdefault(case.source, []).append(curve)

        n_lines = sum(len(curves) for curves in curves_by_source.values())
        if n_lines == 0:
            ax.text(
                0.5,
                0.5,
                f"No design uses {resource_label}",
                transform=ax.transAxes,
                ha="center",
                va="center",
            )
        for source, curves in curves_by_source.items():
            stacked = np.vstack(curves)
            counts = (~np.isnan(stacked)).sum(axis=0)
            # Mean over the source's designs that have a score at each budget
            mean_curve = np.where(
                counts > 0, np.nansum(stacked, axis=0) / np.maximum(counts, 1), np.nan
            )
            ax.plot(
                budgets, mean_curve, color=source_colors[source], lw=MEAN_LW, zorder=4
            )
            sources_present.add(source)
        style_score_row(
            ax,
            f"vs. {resource_label}",
            f"Latency vs. {resource_label} ({n_lines})" if show_row_box else None,
            (0, max_budget),
            ax is axes[-1],
            box_edge_color="black",
            y_limits=y_limits,
        )
        if two_line_ylabel:
            set_two_line_score_ylabel(ax, resource_label)

    finish_figure(
        fig,
        output_dir / filename,
        [
            Line2D([0], [0], color=GREY, alpha=0.8, label="Individual design"),
            *[
                Line2D([0], [0], color=source_colors[source], lw=MEAN_LW, label=f"Mean, {source_label(source)}")
                for source in sources
                if source in sources_present
            ],
        ],
        x_label,
        legend_fontsize=10,
        legend_bold=True,
        legend_y=0.925 if SHOW_SUBTITLE else 0.955,
        rect_top=0.915 if SHOW_SUBTITLE else 0.945,
    )


if __name__ == "__main__":
    dir_cases_plot = [
        dir_case
        for dir_case in DIR_OUTPUT_DATA.iterdir()
        if dir_case.is_dir() and (dir_case / "all_eval_data.json").exists()
    ]

    DIR_FIGURES_SCORES = DIR_FIGURES / "pareto_score_cost_and_runtime_plots"

    case_scores: dict[str, IsoBudgetScores] = {}
    with ProcessPoolExecutor(max_workers=32) as executor:
        futures = {
            executor.submit(_compute_pool_scores, dir_case): dir_case
            for dir_case in dir_cases_plot
        }
        for future in as_completed(futures):
            dir_case = futures[future]
            try:
                result = future.result()
                if result.pool_scores_by_resource:
                    case_scores[dir_case.name] = result
                else:
                    print(f"Skipping case {dir_case.name}: no scoreable points.")
            except Exception as e:
                print(f"Error scoring case {dir_case.name}: {e}")

    make_iso_budget_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_cost",
        "Budget: Cumulative Agent Cost ($)",
        "iso_budget_pareto_score__cost.png",
        "cost",
    )
    make_iso_budget_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_seconds",
        "Budget: Cumulative Agent Time (s)",
        "iso_budget_pareto_score__runtime.png",
        "time",
    )

    # Same plots with the per-iteration scoring: each design's value at a
    # budget is the score of its latest completed iteration's own front.
    make_iso_budget_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_cost",
        "Budget: Cumulative Agent Cost ($)",
        "iso_budget_pareto_score_per_iter__cost.png",
        "cost",
        score_attr="iter_scores_by_resource",
        score_description="latest iteration",
        title="Parameterized Design Pareto Frontier Score / Iso-Cost",
        two_line_ylabel=True,
        show_row_box=False,
        y_limits=(0.0, 1.0),
    )
    make_iso_budget_plot(
        case_scores,
        DIR_FIGURES_SCORES,
        "cumulative_seconds",
        "Budget: Cumulative Agent Time (s)",
        "iso_budget_pareto_score_per_iter__runtime.png",
        "time",
        score_attr="iter_scores_by_resource",
        score_description="latest iteration",
        title="Parameterized Design Pareto Frontier Score / Iso-Runtime",
        two_line_ylabel=True,
        show_row_box=False,
        y_limits=(0.0, 1.0),
    )
    print(f"Done making iso-budget plots for {len(case_scores)} designs")
