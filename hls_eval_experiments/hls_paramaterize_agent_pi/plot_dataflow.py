"""Pareto plots comparing the two dataflow agent runs at one iteration.

Scans the two run directories of exp_dataflow.py for the per-iteration data
files (`iteration_eval_data.json`), keeps the designs that have the chosen
iteration (default: iteration 0) in BOTH runs, and draws one figure per design
in the style of plot_single_case_iterative.py, with one Pareto line per run:

    - agent with no Vitis HLS and no dataflow tools
    - agent with Vitis HLS plus LightningSim / FIFOAdvisor

Latency is the harness's LightningSim latency. Each panel also shows a Pareto
score for each run's front, computed exactly as in plot_pareto_scores.py (the
baseline-anchored hypervolume ratio in log10(x + 1) space, helpers imported from
it), except that P* is the combined front of BOTH runs' iteration-0 points plus
the baseline; the two runs are then scored against that shared P*.

The same scores go into a LaTeX table (default figures/dataflow_results.tex): one
group of rows per design (latency vs. LUTs / FFs / DSPs / BRAMs), a Pareto-score
column per run, and per run the agent's runtime for the iteration (one number per
design, spanning its rows), for the chosen iteration only. The runtime is the
agent's own working time; the harness's evaluation afterwards is not included.

The run directories are only
READ, never written: the runs may still be in progress, so files can appear
(or be half-written) while this script runs. Figures go to a separate folder.

    uv run python hls_eval_experiments/hls_paramaterize_agent_pi/plot_dataflow.py
"""

import argparse
import json
import math
import time
from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.transforms import blended_transform_factory

# The scoring helpers are imported, not copied, so the technique cannot drift.
from plot_pareto_scores import REFERENCE_MARGIN_LOG, _hypervolume, _to_log
from plot_pareto_scores import _pareto_front as _ref_pareto_front
from plot_style_trj import apply_trj_style

# set matplotlib to use 'Agg' backend for headless environments
plt.switch_backend("Agg")

DIR_CURRENT = Path(__file__).resolve().parent

# run key -> data directory. The order is the drawing/legend order.
RUN_DIRS = {
    "no_tools": DIR_CURRENT / "output_data_dataflow__agent_no_vitis_no_tools",
    "tools": DIR_CURRENT / "output_data_dataflow__agent_vitis_and_tools",
}
RUN_LABELS = {
    "no_tools": "No Vitis / no tools",
    "tools": "Vitis + tools",
}
RUN_SHORT_LABELS = {"no_tools": "no tools", "tools": "tools"}


# Deliberately not the blue -> green sweep of the iterative plots (which color
# iterations), nor red (the baseline), so these figures are not confused with them.
RUN_STYLES = {
    "no_tools": {"color": "#8034C2", "marker": "x"},  # purple
    "tools": {"color": "#F28E2B", "marker": "+"},  # orange
}

DIR_FIGURES = DIR_CURRENT / "figures" / "single_agent_run_plots_dataflow"
TEX_FILE = DIR_CURRENT / "figures" / "dataflow_results.tex"
# Designs left out of the LaTeX table only (the plots are not affected). Override
# with --table-exclude (give no names to include every design).
TABLE_EXCLUDED_DESIGNS = ("MultiHeadSelfAttention1",)

# The dataflow runs score latency with LightningSim (the harness injects it next
# to Vitis HLS's own estimate, which is not used here).
LATENCY_KEY = "latency_lightningsim_cycles"
# Short, like the iterative plots (a longer label collides between the panels);
# the subtitle says the latency is LightningSim's.
LATENCY_LABEL = "Latency (cycles)"

# The iteration data files do not carry benchmark tags; every design in these
# runs comes from the same source.
SOURCE_DISPLAY_NAME = "StreamHLS"

RESOURCE_TYPES = {
    "resources_lut_used": ("LUTs Used", "resources_lut_total"),
    "resources_ff_used": ("FFs Used", "resources_ff_total"),
    "resources_dsp_used": ("DSPs Used", "resources_dsp_total"),
    "resources_bram_used": ("BRAMs Used", "resources_bram_total"),
}

# Axes-fraction heights the resource-budget labels alternate between.
LABEL_Y_ROWS = [0.9, 0.72]
# Figure-fraction top of the axes grid, under the title / subtitle / legend.
AXES_TOP = 0.85
# The score box sits at the bottom left, where the best (fast, small) points
# are. Each panel's y axis is extended downward so that this fraction of the
# axes height, at the bottom, is free of data for the box.
SCORE_LEGEND_ROOM = 0.30


# ---- Reading the (possibly still changing) run data ---------------------------


def scan_iteration_files(run_dir: Path) -> dict[str, dict[int, Path]]:
    """{case directory name: {iteration index: path}} for the first sample."""
    found: dict[str, dict[int, Path]] = {}
    if not run_dir.is_dir():
        return found
    for path in sorted(run_dir.glob("*/sample__0/iteration__*/iteration_eval_data.json")):
        case = path.parents[2].name
        iteration = int(path.parent.name.removeprefix("iteration__"))
        found.setdefault(case, {})[iteration] = path
    return found


def load_json(path: Path, attempts: int = 3) -> dict | None:
    """Read-only load. A file the running harness is writing right now can be
    half-written, so retry briefly and otherwise treat it as not there yet."""
    for attempt in range(attempts):
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            if attempt + 1 < attempts:
                time.sleep(1.0)
    return None


def design_name(case: str) -> str:
    """'atax__deepseek_deepseek_v4.1_flash' -> 'atax'."""
    return case.rsplit("__", 1)[0]


def _metrics(point: dict) -> dict | None:
    return ((point.get("vitis_hls_tool_out") or {}).get("data_tool")) or None


def _is_number(value) -> bool:
    return (
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
    )


def _extract_point(point: dict) -> dict | None:
    metrics = _metrics(point)
    if not metrics:
        return None
    try:
        row = {
            "point_index": point.get("point_index"),
            "latency": metrics[LATENCY_KEY],
            **{key: metrics[key] for key in RESOURCE_TYPES},
        }
    except KeyError:
        return None
    if not all(_is_number(row[key]) for key in ("latency", *RESOURCE_TYPES)):
        return None
    return row


def agent_runtime_seconds(iteration: dict) -> float | None:
    """Wall-clock seconds the agent worked on the iteration (container start to
    session export); the harness's evaluation after it finished is not included."""
    seconds = (iteration.get("agent_execution_time") or {}).get("execution_time")
    return float(seconds) if _is_number(seconds) else None


def usable_points(iteration: dict) -> list[dict]:
    """Points that rendered, passed every stage (including LightningSim) and
    have all the plotted metrics."""
    points = []
    for point in iteration.get("points", []):
        if not (point.get("passed") and point.get("render_success")):
            continue
        row = _extract_point(point)
        if row is not None:
            points.append(row)
    return points


def usable_baseline(iteration: dict) -> dict | None:
    baseline = iteration.get("baseline")
    if not baseline or not baseline.get("passed"):
        return None
    return _extract_point(baseline)


def baseline_status(iteration: dict) -> str:
    baseline = iteration.get("baseline")
    if not baseline:
        return "not evaluated"
    if baseline.get("passed"):
        return "passed"
    return baseline.get("lightningsim_status") or "failed"


def resource_totals(iterations: list[dict]) -> dict[str, float]:
    """Device totals (for the resource-budget lines), from any synthesis result
    that has them; failed points still carry them if synthesis ran."""
    totals: dict[str, float] = {}
    for iteration in iterations:
        results = [iteration.get("baseline") or {}, *iteration.get("points", [])]
        for result in results:
            metrics = _metrics(result)
            if not metrics:
                continue
            for _, total_key in RESOURCE_TYPES.values():
                if total_key not in totals and metrics.get(total_key):
                    totals[total_key] = metrics[total_key]
        if len(totals) == len(RESOURCE_TYPES):
            break
    return totals


# ---- Plotting ------------------------------------------------------------------


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
    """Shared axis text/tick styling of the plot family."""
    ax.set_xlabel(resource_label, fontweight="bold")
    ax.set_ylabel(LATENCY_LABEL, fontweight="bold")
    ax.tick_params(which="both", length=4, width=1.0, direction="inout")
    ax.grid(True, which="major")
    ax.grid(True, which="minor", linewidth=0.35, alpha=0.35)


def _set_resource_scale(ax, values: list[float]):
    """Log axis, or symlog when a resource is used at zero somewhere (e.g. no
    BRAM), so zero-resource points are drawn instead of silently dropped."""
    if any(value <= 0 for value in values):
        ax.set_xscale("symlog", linthresh=1)
    else:
        ax.set_xscale("log")


def score_panel(
    points_by_run: dict[str, list[dict]], baseline: dict | None, resource_key: str
) -> dict[str, float] | None:
    """Baseline-anchored hypervolume-ratio score of each run's front, for one
    resource type; the technique of plot_pareto_scores._compute_case_scores.

    Both axes are log10(x + 1). P* is the Pareto front of the baseline and ALL
    runs' points (so the runs are scored against each other's points too). The
    reference point is P*'s worst latency and worst resource plus log10(1.1). A
    run's score is (H(front + baseline) - H(baseline)) / (H(P*) - H(baseline)),
    in [0, 1]; a run with no points scores NaN. Without a usable baseline the
    scores are unanchored, H(front) / H(P*). Returns None when there is nothing
    to score (the resource is never used, or no point beats the baseline).
    """
    baseline_points = _to_log([baseline], resource_key) if baseline else []
    fronts = {
        run: _ref_pareto_front(_to_log(points, resource_key), resource_key)
        for run, points in points_by_run.items()
    }
    all_front_points = [point for front in fronts.values() for point in front]
    if not all_front_points:
        return None
    if all(point[resource_key] == 0 for point in all_front_points + baseline_points):
        return None

    combined_front = _ref_pareto_front(all_front_points + baseline_points, resource_key)
    ref_latency = REFERENCE_MARGIN_LOG + max(p["latency"] for p in combined_front)
    ref_resource = REFERENCE_MARGIN_LOG + max(p[resource_key] for p in combined_front)

    def hv(points: list[dict]) -> float:
        return _hypervolume(points, resource_key, ref_resource, ref_latency)

    hv_base = hv(baseline_points)
    denominator = hv(combined_front) - hv_base
    if denominator <= 0:
        return None
    return {
        run: (hv(front + baseline_points) - hv_base) / denominator
        if front
        else math.nan
        for run, front in fronts.items()
    }


def pick_baseline(iterations_by_run: dict[str, dict]) -> dict | None:
    """The baseline (every run measures the same unmodified design): the first
    usable one, in run order."""
    for iteration in iterations_by_run.values():
        baseline = usable_baseline(iteration)
        if baseline is not None:
            return baseline
    return None


def case_scores(iterations_by_run: dict[str, dict]) -> dict[str, dict[str, float] | None]:
    """{resource key: {run: score} or None} for one design: the numbers shown on
    the plots and in the table. None = not scored (the resource is never used,
    no run has a usable point, or nothing beats the baseline)."""
    points_by_run = {run: usable_points(it) for run, it in iterations_by_run.items()}
    baseline = pick_baseline(iterations_by_run)
    return {
        resource_key: score_panel(points_by_run, baseline, resource_key)
        for resource_key in RESOURCE_TYPES
    }


def _format_score(score: float | None) -> str:
    return "n/a" if score is None or math.isnan(score) else f"{score:.2f}"


def make_plot(
    case: str,
    iterations_by_run: dict[str, dict],
    iteration_index: int,
    output_dir: Path,
) -> Path | None:
    points_by_run = {run: usable_points(it) for run, it in iterations_by_run.items()}
    if not any(points_by_run.values()):
        print(f"  skipping {case}: no run has a usable point at iteration {iteration_index}")
        return None

    baselines = {run: usable_baseline(it) for run, it in iterations_by_run.items()}
    baseline_point = next((b for b in baselines.values() if b is not None), None)
    present = [b for b in baselines.values() if b is not None]
    if len(present) == 2 and any(
        present[0][key] != present[1][key] for key in ("latency", *RESOURCE_TYPES)
    ):
        print(f"  note: the two runs' baselines for {case} differ; drawing the first")
    totals = resource_totals(list(iterations_by_run.values()))

    run_status = {}
    for run, iteration in iterations_by_run.items():
        n_points = len(iteration.get("points", []))
        run_status[run] = (len(points_by_run[run]), n_points)

    legend_handles = []
    if baseline_point is not None:
        legend_handles.append(
            Line2D([0], [0], color="red", marker="o", linestyle="none", label="Baseline")
        )
    for run in RUN_DIRS:
        style = RUN_STYLES[run]
        label = RUN_LABELS[run]
        if not points_by_run[run]:
            label += " (none passed)"
        legend_handles.append(
            Line2D(
                [0],
                [0],
                color=style["color"],
                marker=style["marker"],
                linestyle="-",
                label=label,
            )
        )

    if baseline_point is None:
        print(
            f"  WARNING: {case}: no usable baseline; scores are NOT "
            "baseline-anchored (0 does not mean 'no better than the baseline')."
        )
    panel_scores = case_scores(iterations_by_run)

    apply_trj_style()
    fig, axes = plt.subplots(2, 2, figsize=(7, 5.6))
    for ax, (resource_key, (resource_label, total_key)) in zip(
        axes.flat, RESOURCE_TYPES.items()
    ):
        all_values = [
            point[resource_key] for points in points_by_run.values() for point in points
        ]
        if baseline_point is not None:
            all_values.append(baseline_point[resource_key])
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
            ax.tick_params(labelbottom=False, labelleft=False)
            continue

        if baseline_point is not None:
            ax.scatter(
                [baseline_point[resource_key]],
                [baseline_point["latency"]],
                color="red",
                marker="o",
                s=22,
                zorder=5,
            )

        for run in RUN_DIRS:
            points = points_by_run[run]
            if not points:
                continue
            style = RUN_STYLES[run]
            ax.scatter(
                [point[resource_key] for point in points],
                [point["latency"] for point in points],
                color=style["color"],
                marker=style["marker"],
                s=22,
            )
            front = _pareto_front(points, resource_key)
            front_x = [point[resource_key] for point in front]
            front_y = [point["latency"] for point in front]
            if len(front) == 1:
                ax.plot(
                    front_x,
                    front_y,
                    color=style["color"],
                    marker="o",
                    markersize=20,
                    markerfacecolor=style["color"],
                    markeredgecolor=style["color"],
                    alpha=0.3,
                    linestyle="none",
                    zorder=-5,
                )
            else:
                ax.plot(
                    front_x,
                    front_y,
                    color=style["color"],
                    linestyle="-",
                    linewidth=1.5,
                    zorder=-5,
                )

        total_resources = totals.get(total_key)
        if total_resources:
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
                # Neighboring budget lines are close on the log axis, so
                # alternate the label height between two rows.
                ax.text(
                    vline_x,
                    LABEL_Y_ROWS[label_row % len(LABEL_Y_ROWS)],
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
        _set_resource_scale(ax, all_values)
        ax.set_yscale("log")
        _style_panel(ax, resource_label)

        # Make room under the data for the score box (log y axis).
        y_low, y_high = ax.get_ylim()
        span = math.log10(y_high / y_low)
        ax.set_ylim(y_high / 10 ** (span / (1 - SCORE_LEGEND_ROOM)), y_high)

        scores = panel_scores[resource_key]
        score_handles = [
            Line2D(
                [0],
                [0],
                color=RUN_STYLES[run]["color"],
                marker=RUN_STYLES[run]["marker"],
                linestyle="-",
                label=f"{RUN_SHORT_LABELS[run].capitalize()}: "
                f"{_format_score(None if scores is None else scores[run])}",
            )
            for run in RUN_DIRS
        ]
        score_legend = ax.legend(
            handles=score_handles,
            loc="lower left",
            title="Pareto score",
            fontsize=7,
            title_fontsize=7,
            prop={"size": 7, "weight": "bold"},
            frameon=True,
            facecolor="white",
            edgecolor="black",
            framealpha=0.9,
            borderpad=0.4,
            handlelength=1.6,
            handletextpad=0.5,
            labelspacing=0.25,
        )
        score_legend.get_frame().set_linewidth(0.6)
        score_legend.set_zorder(20)

    subtitle_parts = [
        f"{RUN_SHORT_LABELS[run]} {passed}/{total}"
        for run, (passed, total) in run_status.items()
    ]
    subtitle = (
        f"Iteration {iteration_index} pass rates: "
        + ", ".join(subtitle_parts)
        + " (LightningSim latency)"
    )
    baseline_notes = {
        run: baseline_status(it)
        for run, it in iterations_by_run.items()
        if baselines[run] is None
    }
    if baseline_notes and baseline_point is None:
        subtitle += "; baseline: " + "/".join(sorted(set(baseline_notes.values())))

    fig.suptitle(
        f'"{design_name(case)}" from {SOURCE_DISPLAY_NAME}', y=0.995, fontweight="bold"
    )
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
    fig.subplots_adjust(top=AXES_TOP)

    for resource_key, scores in panel_scores.items():
        label = RESOURCE_TYPES[resource_key][0]
        shown = (
            "not scored (unused resource, or nothing beats the baseline)"
            if scores is None
            else ", ".join(
                f"{RUN_SHORT_LABELS[run]} {_format_score(score)}"
                for run, score in scores.items()
            )
        )
        print(f"    {label:12} {shown}")

    output_dir.mkdir(parents=True, exist_ok=True)
    fp_fig = output_dir / f"pareto_front_dataflow_iter{iteration_index}__{case}.png"
    fig.savefig(fp_fig, bbox_inches="tight", pad_inches=0.02, dpi=300)
    plt.close(fig)
    return fp_fig


# ---- LaTeX table ---------------------------------------------------------------

_LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}


def _latex_escape(text: str) -> str:
    return "".join(_LATEX_ESCAPES.get(char, char) for char in text)


def _tex_score(score: float | None, bold: bool) -> str:
    if score is None or math.isnan(score):
        return "--"
    text = f"{score:.2f}"
    return rf"\textbf{{{text}}}" if bold else text


def _better_run(scores: dict[str, float] | None) -> str | None:
    """The run with the higher displayed score, if both have one and they differ."""
    if scores is None:
        return None
    values = {run: scores.get(run) for run in RUN_DIRS}
    if any(v is None or math.isnan(v) for v in values.values()):
        return None
    rounded = {run: round(v, 2) for run, v in values.items()}
    if len(set(rounded.values())) == 1:
        return None
    return max(rounded, key=rounded.get)


def _tex_runtime(seconds: float | None) -> str:
    return "--" if seconds is None else f"{seconds / 60:.1f}"


def write_results_tex(
    rows: list[
        tuple[str, dict[str, dict[str, float] | None], dict[str, float | None]]
    ],
    iteration_index: int,
    path: Path,
    excluded: list[str],
    omitted: list[str] | None = None,
) -> None:
    """A bare booktabs `tabular` (like the repo's other generated tables; put it
    inside your own table environment): one row group per design, one row per
    resource type, a Pareto-score column per run, then an agent-runtime column
    per run with one number per design spanning its rows. The higher score of a
    row is bold.

    `rows` is (design, {resource key: {run: score} or None}, {run: agent seconds
    or None}). `excluded` names designs without the iteration in both runs;
    `omitted` names designs left out of the table by choice.
    """
    n_resources = len(RESOURCE_TYPES)
    lines = [
        f"% Generated by plot_dataflow.py on {time.strftime('%Y-%m-%d %H:%M')}; do not edit by hand.",
        f"% Iteration {iteration_index} only, {len(rows)} design(s) with that iteration in both runs.",
        "% Requires: \\usepackage{booktabs,multirow}",
        "% Pareto score = baseline-anchored hypervolume ratio in log10(x+1) space of a run's",
        "% latency-vs-resource front, against P*, the combined front of BOTH runs' iteration points",
        "% and the baseline (see plot_pareto_scores.py); higher is better, the larger score of a",
        "% row is bold, -- = not scored. Latency is LightningSim's.",
        "% Agent runtime = minutes the agent worked on the iteration (agent_execution_time), one",
        "% value per design; the harness's checking, synthesis and simulation afterwards is NOT included.",
    ]
    if excluded:
        lines.append(f"% Not included (iteration {iteration_index} missing in a run): " + ", ".join(excluded))
    if omitted:
        lines.append("% Left out of this table by choice: " + ", ".join(omitted))
    lines += [
        "\\begin{tabular}{llcccc}",
        "\\toprule",
        " & & \\multicolumn{2}{c}{\\textbf{Pareto score}} & \\multicolumn{2}{c}{\\textbf{Agent runtime (min)}} \\\\",
        "\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}",
        "\\textbf{Design} & \\textbf{Objective} & \\textbf{No tools} & \\textbf{Tools} & \\textbf{No tools} & \\textbf{Tools} \\\\",
    ]
    for design, scores_by_resource, runtimes in rows:
        lines.append("\\midrule")
        for index, (resource_key, (resource_label, _)) in enumerate(RESOURCE_TYPES.items()):
            scores = scores_by_resource.get(resource_key)
            best = _better_run(scores)
            cells = {
                run: _tex_score(None if scores is None else scores.get(run), run == best)
                for run in RUN_DIRS
            }
            if index == 0:
                design_cell = f"\\multirow{{{n_resources}}}{{*}}{{{_latex_escape(design)}}}"
                runtime_cells = {
                    run: f"\\multirow{{{n_resources}}}{{*}}{{{_tex_runtime(runtimes.get(run))}}}"
                    for run in RUN_DIRS
                }
            else:
                design_cell = ""
                runtime_cells = {run: "" for run in RUN_DIRS}
            objective = "Latency vs.\\ " + _latex_escape(resource_label.replace(" Used", ""))
            lines.append(
                f"{design_cell} & {objective} & {cells['no_tools']} & {cells['tools']}"
                f" & {runtime_cells['no_tools']} & {runtime_cells['tools']} \\\\"
            )
    lines += ["\\bottomrule", "\\end{tabular}", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines))


# ---- Main ----------------------------------------------------------------------


def _assert_output_outside_run_dirs(output_dir: Path):
    """The runs may still be going; never put anything inside their folders."""
    resolved = output_dir.resolve()
    for run_dir in RUN_DIRS.values():
        if resolved == run_dir.resolve() or run_dir.resolve() in resolved.parents:
            raise SystemExit(f"Refusing to write inside the run directory {run_dir}")


def _format_iterations(iterations: dict[int, Path] | None) -> str:
    return ",".join(str(i) for i in sorted(iterations)) if iterations else "-"


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--iteration",
        type=int,
        default=0,
        help="iteration that must be present in both runs and is plotted (default 0)",
    )
    parser.add_argument("--output-dir", type=Path, default=DIR_FIGURES)
    parser.add_argument(
        "--table-exclude",
        nargs="*",
        default=list(TABLE_EXCLUDED_DESIGNS),
        metavar="DESIGN",
        help="designs to leave out of the LaTeX table only "
        f"(default: {' '.join(TABLE_EXCLUDED_DESIGNS)}; pass no names to keep all)",
    )
    parser.add_argument(
        "--tex-file",
        type=Path,
        default=TEX_FILE,
        help="where to write the LaTeX table of the Pareto scores",
    )
    args = parser.parse_args()
    _assert_output_outside_run_dirs(args.output_dir)
    _assert_output_outside_run_dirs(args.tex_file)

    scans = {run: scan_iteration_files(run_dir) for run, run_dir in RUN_DIRS.items()}
    cases = sorted(set().union(*(scan.keys() for scan in scans.values())))
    if not cases:
        raise SystemExit("No iteration data found in either run directory.")

    print(f"Iterations available per case (plotting iteration {args.iteration}):")
    width = max(len(design_name(case)) for case in cases)
    print(f"  {'design':{width}}  {'no tools':>10}  {'tools':>10}  plotted")
    to_plot = []
    excluded = []
    for case in cases:
        per_run = {run: scans[run].get(case) for run in RUN_DIRS}
        has_all = all(it is not None and args.iteration in it for it in per_run.values())
        if has_all:
            to_plot.append(case)
        else:
            excluded.append(design_name(case))
        missing = [
            RUN_SHORT_LABELS[run]
            for run, it in per_run.items()
            if it is None or args.iteration not in it
        ]
        note = "yes" if has_all else "no (iteration missing in: " + ", ".join(missing) + ")"
        print(
            f"  {design_name(case):{width}}  "
            f"{_format_iterations(per_run['no_tools']):>10}  "
            f"{_format_iterations(per_run['tools']):>10}  {note}"
        )

    print(f"\nPlotting {len(to_plot)} design(s) to {args.output_dir}")
    written = 0
    table_rows = []
    omitted = []
    for case in to_plot:
        loaded = {
            run: load_json(scans[run][case][args.iteration]) for run in RUN_DIRS
        }
        if any(data is None for data in loaded.values()):
            print(f"  skipping {case}: an iteration file is unreadable (still being written?)")
            continue
        if design_name(case) in args.table_exclude:
            omitted.append(design_name(case))
        else:
            table_rows.append(
                (
                    design_name(case),
                    case_scores(loaded),
                    {run: agent_runtime_seconds(loaded[run]) for run in RUN_DIRS},
                )
            )
        fp = make_plot(case, loaded, args.iteration, args.output_dir)
        if fp is not None:
            written += 1
            print(f"  wrote {fp.name}")
    print(f"\nDone: {written} figure(s).")
    if table_rows:
        write_results_tex(table_rows, args.iteration, args.tex_file, excluded, omitted)
        print(f"Wrote the LaTeX table ({len(table_rows)} design(s)): {args.tex_file}")
    else:
        print("No paired designs yet, so no LaTeX table was written.")


if __name__ == "__main__":
    main()
