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
    fig.text(0.5, 0.945, subtitle, ha="center", va="top", fontsize=10)
    return fig, list(axes[:, 0])


def style_score_row(
    ax,
    y_label: str,
    box_label: str,
    x_range: tuple[float, float] | None,
    is_last: bool,
    box_edge_color=None,
):
    """Row styling: white background, boxed label (bottom right, where
    the rising score curves leave room), 0..1 y axis, inout ticks."""
    if x_range is not None:
        ax.set_xlim(*x_range)
    dark = box_edge_color or tuple(0.6 * c for c in mcolors.to_rgb(ROW_ACCENT_COLOR))
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
            boxstyle="round,pad=0.4", facecolor="white", edgecolor=dark, linewidth=0.8
        ),
        zorder=10,
    )
    ax.set_ylim(-0.04, 1.04)
    ax.yaxis.set_major_locator(MultipleLocator(0.2))
    ax.set_ylabel(y_label, fontweight="bold")
    ax.yaxis.set_label_coords(-0.1, 0.5)
    ax.yaxis.label.set_verticalalignment("center")
    ax.tick_params(axis="x", which="both", length=5, width=1.0, direction="inout")
    ax.tick_params(axis="x", labelbottom=is_last)


def finish_figure(fig, out_fp, legend_handles, x_label: str):
    fig.axes[-1].set_xlabel(x_label, fontweight="bold")
    fig.legend(
        handles=legend_handles,
        loc="upper center",
        bbox_to_anchor=(0.5, 0.925),
        ncol=3,
        fontsize=8,
        frameon=False,
    )
    fig.tight_layout(rect=[0, 0, 1, 0.905], h_pad=1.0)
    out_fp.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_fp, bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)
