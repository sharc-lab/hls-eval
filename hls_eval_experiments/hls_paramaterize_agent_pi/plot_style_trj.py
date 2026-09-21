"""Shared plot styling, matching the look of the old plot_trj trajectory plots:
dotted grid, compact stacked rows, faint gray per-design lines, thick average
lines with white-filled markers, and rows with a boxed row label.
"""

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

GREY = "0.72"
GREY_LW = 1.0
GREY_ALPHA = 0.40
MEAN_LW = 2.4

# Colors for benchmark sources, and the accent color of the row labels' borders
SOURCE_BASE_COLORS = ["#E63946", "#F4A261", "#2A9D8F", "#8BCAFF", "#8034C2"]
ROW_ACCENT_COLOR = "#8034C2"

# Display labels for benchmark sources (the raw `benchmark_case_tags` values).
# Plots should show source_label(key), never the raw key; keep keys raw
# everywhere else (grouping, color maps). Unmapped keys fall back to themselves.
SOURCE_LABELS = {
    "athena_crypto": "ATHENa",
    "llm4pqc_benchmarks": "PQC",
    "polybench__fixed__small": "PolyBench",
    "rodinia_clean": "Rodinia",
}


def source_label(source: str) -> str:
    """Display label for a benchmark source key, or a comma/slash-joined run of
    keys (multi-tag cases)."""
    for sep in (", ", "/"):
        if sep in source:
            return sep.join(source_label(part) for part in source.split(sep))
    return SOURCE_LABELS.get(source, source)


def apply_trj_style():
    plt.rcParams.update(
        {
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "font.family": "sans-serif",
            "font.sans-serif": ["DejaVu Sans"],
            "font.size": 10,
            "axes.titlesize": 11,
            "axes.labelsize": 10.5,
            "xtick.labelsize": 9.5,
            "ytick.labelsize": 9.5,
            "figure.titlesize": 13,
            "axes.grid": True,
            "grid.linestyle": ":",
            "grid.linewidth": 0.55,
            "grid.alpha": 0.50,
            "lines.linewidth": 2.2,
            "legend.frameon": False,
        }
    )


def source_color_map(sources: list[str]) -> dict[str, str]:
    return {
        source: SOURCE_BASE_COLORS[i % len(SOURCE_BASE_COLORS)]
        for i, source in enumerate(sources)
    }


def new_stacked_figure(n_rows: int, title: str, subtitle: str):
    """Compact stacked rows sharing the x axis, with a bold title and a subtitle;
    returns the figure and a flat list of axes."""
    apply_trj_style()
    fig, axes = plt.subplots(
        n_rows, 1, figsize=(6.5, 1.2 * n_rows + 1.4), sharex=True, squeeze=False
    )
    fig.suptitle(title, y=0.985, fontweight="bold")
    if subtitle:
        fig.text(0.5, 0.945, subtitle, ha="center", va="top", fontsize=10)
    return fig, list(axes[:, 0])


def style_score_row(
    ax,
    y_label: str,
    box_label: str | None,
    x_range: tuple[float, float] | None,
    is_last: bool,
    box_edge_color=None,
    y_limits: tuple[float, float] = (-0.04, 1.04),
):
    """Row styling: white background, boxed label (bottom right, where
    the rising score curves leave room; omitted when box_label is None/empty),
    0..1 y axis, inout ticks."""
    if x_range is not None:
        ax.set_xlim(*x_range)
    if box_label:
        dark = box_edge_color or tuple(
            0.6 * c for c in mcolors.to_rgb(ROW_ACCENT_COLOR)
        )
        ax.text(
            0.985,
            0.15,
            box_label,
            ha="right",
            va="center",
            fontsize=7.25,
            fontweight="bold",
            transform=ax.transAxes,
            bbox=dict(
                boxstyle="round,pad=0.4",
                facecolor="white",
                edgecolor=dark,
                linewidth=0.8,
            ),
            zorder=10,
        )
    ax.set_ylim(*y_limits)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.set_ylabel(y_label, fontweight="bold")
    ax.yaxis.set_label_coords(-0.1, 0.5)
    ax.yaxis.label.set_verticalalignment("center")
    ax.tick_params(axis="x", which="both", length=5, width=1.0, direction="inout")
    ax.tick_params(axis="x", labelbottom=is_last)


def set_two_line_score_ylabel(ax, resource_label: str, title: str = "Pareto Score"):
    """Two-line y label: a bold `title`, with a smaller regular-weight
    "(Lat. vs. <resource>)" line between it and the axis."""
    ax.set_ylabel(title, fontweight="bold")
    ax.yaxis.set_label_coords(-0.135, 0.5)
    ax.text(
        -0.098,
        0.5,
        f"(Lat. vs. {resource_label})",
        transform=ax.transAxes,
        rotation=90,
        ha="center",
        va="center",
        fontsize=8.5,
    )


def finish_figure(
    fig,
    out_fp,
    legend_handles,
    x_label: str,
    legend_fontsize: float = 8,
    legend_bold: bool = False,
    legend_y: float = 0.925,
    rect_top: float = 0.905,
):
    """legend_y is the figure-fraction top of the legend; rect_top is the
    figure-fraction top of the area the axes are laid out in."""
    fig.axes[-1].set_xlabel(x_label, fontweight="bold")
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, legend_y),
        ncol=3,
        prop={"size": legend_fontsize, "weight": "bold" if legend_bold else "normal"},
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, rect_top], h_pad=1.0)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fp, bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)
