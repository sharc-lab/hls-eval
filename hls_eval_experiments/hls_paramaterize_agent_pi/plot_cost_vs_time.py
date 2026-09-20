"""Cumulative agent cost vs. cumulative agent time: one point per design per
iteration, at the design's total agent time (x, seconds) and total agent cost (y,
dollars) through the end of that iteration. All samples of one iteration share the
same cost and time, so they land on the same point; a thin line joins a design's
iterations in order.
"""

from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D

from plot_pareto_scores_cost_and_runtime import (
    DIR_FIGURES,
    DIR_OUTPUT_DATA,
    CaseData,
    _load_case_data,
)
from plot_style_trj import GREY, GREY_ALPHA, GREY_LW, apply_trj_style, source_color_map


def make_cost_vs_time_plot(cases: dict[str, CaseData], output_dir: Path):
    apply_trj_style()
    sources = sorted({case.source for case in cases.values()})
    source_colors = source_color_map(sources)

    fig, ax = plt.subplots(figsize=(6.5, 4.6))
    for case in cases.values():
        ax.plot(
            case.cumulative_seconds,
            case.cumulative_cost,
            color=GREY,
            linewidth=GREY_LW,
            alpha=GREY_ALPHA,
            zorder=2,
        )
    for source in sources:
        source_cases = [case for case in cases.values() if case.source == source]
        ax.scatter(
            [x for case in source_cases for x in case.cumulative_seconds],
            [y for case in source_cases for y in case.cumulative_cost],
            s=30,
            color=source_colors[source],
            edgecolor="white",
            linewidth=0.6,
            zorder=3,
        )
    all_seconds = [x for case in cases.values() for x in case.cumulative_seconds]
    all_costs = [y for case in cases.values() for y in case.cumulative_cost]
    correlation = np.corrcoef(all_seconds, all_costs)[0, 1]
    ax.text(
        0.03,
        0.95,
        f"Pearson r = {correlation:.3f}",
        transform=ax.transAxes,
        ha="left",
        va="top",
        fontsize=9,
        fontweight="bold",
        bbox=dict(
            boxstyle="round,pad=0.4", facecolor="white", edgecolor="black", linewidth=0.8
        ),
        zorder=10,
    )
    ax.set_xlim(left=0)
    ax.set_ylim(bottom=0)
    ax.set_xlabel("Cumulative Agent Time (s)", fontweight="bold")
    ax.set_ylabel("Cumulative Agent Cost ($)", fontweight="bold")
    ax.tick_params(which="both", length=5, width=1.0, direction="inout")
    fig.suptitle("Cumulative Agent Cost vs. Agent Time", y=0.985, fontweight="bold")
    fig.text(0.5, 0.925, f"{sum(len(c.cumulative_cost) for c in cases.values())} points from {len(cases)} designs | one per design per iteration",
        ha="center",
        va="top",
        fontsize=10,
    )
    fig.legend(
        handles=[
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="none",
                markersize=7,
                color=source_colors[source],
                markeredgecolor="white",
                label=f"{source} ({sum(case.source == source for case in cases.values())})",
            )
            for source in sources
        ],
        loc="upper center",
        bbox_to_anchor=(0.5, 0.905),
        ncol=2,
        fontsize=8,
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.87])

    output_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(
        output_dir / "cost_vs_time__all_designs.png",
        bbox_inches="tight",
        pad_inches=0.02,
        dpi=300,
    )
    plt.close(fig)


if __name__ == "__main__":
    dir_cases = [
        dir_case
        for dir_case in DIR_OUTPUT_DATA.iterdir()
        if dir_case.is_dir() and (dir_case / "all_eval_data.json").exists()
    ]

    cases: dict[str, CaseData] = {}
    with ProcessPoolExecutor(max_workers=32) as executor:
        futures = {executor.submit(_load_case_data, d): d for d in dir_cases}
        for future in as_completed(futures):
            dir_case = futures[future]
            try:
                cases[dir_case.name] = future.result()
            except Exception as e:
                print(f"Error loading case {dir_case.name}: {e}")

    make_cost_vs_time_plot(cases, DIR_FIGURES / "pareto_score_cost_and_runtime_plots")
    print(f"Done making cost vs. time plot for {len(cases)} designs")
