#!/usr/bin/env python3
"""Status overview of the dataflow experiment (exp_dataflow.py) while it runs.

Prints, for the two runs (agent with Vitis + tools, agent with neither):

  1. Overview: for every design, the stage each run is at.
  2. Per-run detail: iteration, stage, files written, agent activity and cost,
     read from the agents' live session logs.
  3. Harness verdicts for every finished iteration (baseline, per-point
     LightningSim outcome, Pareto points, speedup over the baseline).
  4. Infrastructure: running agent containers, Vitis / LightningSim processes,
     free disk space.

Stages of one iteration of one design:

  exploring      the agent is working; it has not written design_space.jsonl yet
  writing files  design_space.jsonl was written in this iteration; the agent is
                 finalizing / validating
  evaluating     the agent finished; the harness is checking, synthesizing and
                 simulating the points (shows how many points are done)
  done           the harness finished the iteration (iteration_eval_data.json)

Everything is only READ: nothing is written to the run directories (or
anywhere else), so it is safe to run at any time, and often. Standard library
only. Usage:

    python3 hls_eval_experiments/hls_paramaterize_agent_pi/status_dataflow.py
    python3 .../status_dataflow.py --watch 120     # refresh every 2 minutes
    python3 .../status_dataflow.py --quick         # skip the (slower) verdicts
    python3 .../status_dataflow.py --last-action   # also show each agent's last command
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

DIR_CURRENT = Path(__file__).resolve().parent

# run key -> data directory (the order is the display order)
RUN_DIRS = {
    "no_tools": DIR_CURRENT / "output_data_dataflow__agent_no_vitis_no_tools",
    "tools": DIR_CURRENT / "output_data_dataflow__agent_vitis_and_tools",
}
RUN_TITLES = {
    "no_tools": "No Vitis / no tools",
    "tools": "Vitis + tools",
}
DOCKER_IMAGE = "hls-eval-agent-pi-dataflow"

# An agent silent for longer than this is flagged (long model generations are
# normal, so this only marks it; it does not mean the agent is stuck).
IDLE_FLAG_SECONDS = 10 * 60

LATENCY_KEY = "latency_lightningsim_cycles"

# The agents run Vitis through their own scripts too, so this is approximate.
VITIS_LAUNCH_RE = re.compile(
    r"vitis_hls\s+-f|vitis_hls\s+\S+\.tcl|syn\.sh|synth\w*\.sh|run_?point"
)
LIGHTNINGSIM_RE = re.compile(r"\blightningsim\s+\S")
FIFO_ADVISOR_RE = re.compile(r"\bfifo-advisor\s+\S")

STAGE_ORDER = ["starting", "exploring", "writing files", "evaluating", "done"]


# ---- Reading the (possibly still changing) run data ---------------------------


def parse_time(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def read_json_lines(path: Path) -> list[dict]:
    rows = []
    try:
        text = path.read_text(errors="replace")
    except OSError:
        return rows
    for line in text.splitlines():
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass  # the line being written right now
    return rows


def load_json(path: Path) -> dict | None:
    """Read-only; a file being written right now may not parse yet."""
    for attempt in range(3):
        try:
            return json.loads(path.read_text())
        except (json.JSONDecodeError, OSError):
            time.sleep(0.5 * (attempt + 1))
    return None


def count_lines(path: Path) -> int:
    try:
        return len([line for line in path.read_text().splitlines() if line.strip()])
    except OSError:
        return 0


@dataclass
class SessionInfo:
    started: datetime | None = None
    last_event: datetime | None = None
    messages: int = 0
    tool_calls: int = 0
    vitis_launches: int = 0
    lightningsim_runs: int = 0
    fifo_advisor_runs: int = 0
    cost: float = 0.0
    last_action: str = ""


def parse_session(path: Path) -> SessionInfo:
    info = SessionInfo()
    rows = read_json_lines(path)
    if not rows:
        return info
    info.started = parse_time(rows[0]["timestamp"])
    info.last_event = parse_time(rows[-1]["timestamp"])
    for row in rows:
        message = row.get("message") or {}
        if row.get("type") != "message":
            continue
        info.messages += 1
        if message.get("role") != "assistant":
            continue
        info.cost += ((message.get("usage") or {}).get("cost") or {}).get("total", 0.0)
        for content in message.get("content", []):
            if content.get("type") != "toolCall":
                continue
            info.tool_calls += 1
            arguments = content.get("arguments") or {}
            command = arguments.get("command") or ""
            info.vitis_launches += len(VITIS_LAUNCH_RE.findall(command))
            info.lightningsim_runs += len(LIGHTNINGSIM_RE.findall(command))
            info.fifo_advisor_runs += len(FIFO_ADVISOR_RE.findall(command))
            shown = command.strip().splitlines()[0] if command.strip() else json.dumps(arguments)
            info.last_action = f"[{content.get('name')}] {shown}"
    return info


@dataclass
class IterationStatus:
    design: str
    iteration: int
    stage: str
    path: Path
    ds_lines: int = 0
    points_done: int = 0
    session: SessionInfo | None = None
    harness_done: bool = False

    def stage_label(self) -> str:
        if self.stage == "evaluating" and self.ds_lines:
            return f"evaluating {self.points_done}/{self.ds_lines}"
        return self.stage


def design_name(case: str) -> str:
    """'atax__deepseek_deepseek_v4.1_flash' -> 'atax'."""
    return case.rsplit("__", 1)[0]


def iteration_status(case: str, iteration_dir: Path) -> IterationStatus:
    iteration = int(iteration_dir.name.rsplit("__", 1)[1])
    status = IterationStatus(design_name(case), iteration, "starting", iteration_dir)
    sessions = sorted(iteration_dir.glob("agent_run_dir/.pi/sessions/*.jsonl"))
    if sessions:
        status.session = parse_session(sessions[-1])

    design_space = iteration_dir / "agent_run_dir" / "design_space.jsonl"
    status.ds_lines = count_lines(design_space)
    # Later iterations start from a copy of the previous design_space.jsonl (the
    # copy keeps its old modification time), so only a file modified after the
    # session started counts as written by this iteration's agent.
    written_now = False
    if status.ds_lines and status.session and status.session.started:
        try:
            written_now = design_space.stat().st_mtime > status.session.started.timestamp()
        except OSError:
            pass

    status.points_done = len(list(iteration_dir.glob("points/point__*/result.json")))
    status.harness_done = (iteration_dir / "iteration_eval_data.json").is_file()
    if status.harness_done:
        status.stage = "done"
    elif (iteration_dir / "agent_output.txt").is_file():
        status.stage = "evaluating"
    elif written_now:
        status.stage = "writing files"
    elif status.session:
        status.stage = "exploring"
    return status


def scan_run(run_dir: Path) -> dict[str, dict[int, IterationStatus]]:
    """{case directory name: {iteration index: status}} for the first sample."""
    found: dict[str, dict[int, IterationStatus]] = {}
    if not run_dir.is_dir():
        return found
    for iteration_dir in sorted(run_dir.glob("*/sample__0/iteration__*")):
        case = iteration_dir.parents[1].name
        status = iteration_status(case, iteration_dir)
        found.setdefault(case, {})[status.iteration] = status
    return found


def latest(iterations: dict[int, IterationStatus]) -> IterationStatus:
    return iterations[max(iterations)]


# ---- Formatting helpers ---------------------------------------------------------


def minutes(seconds: float) -> str:
    return f"{seconds / 60:.0f}"


def summarize_stages(statuses: list[IterationStatus]) -> str:
    counts = Counter(status.stage for status in statuses)
    return ", ".join(f"{counts[s]} {s}" for s in STAGE_ORDER if counts[s]) or "nothing yet"


def table(rows: list[list[str]], header: list[str], left: set[int]) -> list[str]:
    """Fixed-width table; the columns in `left` are left-aligned, others right."""
    widths = [max(len(str(x)) for x in col) for col in zip(header, *rows)]

    def fmt(row):
        cells = []
        for i, (cell, width) in enumerate(zip(row, widths)):
            cells.append(str(cell).ljust(width) if i in left else str(cell).rjust(width))
        return "  ".join(cells).rstrip()

    return [fmt(header), fmt(["-" * w for w in widths]), *(fmt(row) for row in rows)]


# ---- Report sections ------------------------------------------------------------


def report_overview(scans: dict[str, dict], n_iters: int) -> list[str]:
    cases = sorted(set().union(*(scan.keys() for scan in scans.values())))
    rows = []
    for case in cases:
        row = [design_name(case)]
        for run in RUN_DIRS:
            iterations = scans[run].get(case)
            if not iterations:
                row.append("-")
                continue
            status = latest(iterations)
            finished_all = status.iteration >= n_iters - 1 and status.stage == "done"
            row.append("ALL DONE" if finished_all else f"it{status.iteration} {status.stage_label()}")
        rows.append(row)
    header = ["design", *(RUN_TITLES[run] for run in RUN_DIRS)]
    lines = ["OVERVIEW: the stage each design is at (iteration, stage)", ""]
    lines += table(rows, header, left=set(range(len(header))))
    lines.append("")
    for run in RUN_DIRS:
        statuses = [latest(its) for its in scans[run].values()]
        lines.append(f"  {RUN_TITLES[run]:20} latest iterations: {summarize_stages(statuses)}")
    return lines


def report_run_detail(
    run: str, scan: dict[str, dict], now: datetime, last_action: bool
) -> list[str]:
    lines = [f"{RUN_TITLES[run].upper()}  ({RUN_DIRS[run].name})", ""]
    if not scan:
        return lines + ["  no data yet"]
    rows, notes = [], []
    total_cost = 0.0
    for case in sorted(scan):
        status = latest(scan[case])
        session = status.session
        total_cost += sum(s.session.cost for s in scan[case].values() if s.session)
        if session and session.started and session.last_event:
            if status.stage in ("evaluating", "done"):
                # The agent has finished: show how long it worked, not the time since.
                running = minutes((session.last_event - session.started).total_seconds())
                idle = "-"
            else:
                running = minutes((now - session.started).total_seconds())
                idle_seconds = (now - session.last_event).total_seconds()
                idle = f"{idle_seconds:.0f}" + ("*" if idle_seconds > IDLE_FLAG_SECONDS else "")
        else:
            running, idle = "-", "-"
        rows.append(
            [
                status.design,
                status.stage_label(),
                str(status.iteration),
                str(status.ds_lines),
                str(session.vitis_launches) if session else "-",
                str(session.lightningsim_runs) if session else "-",
                str(session.fifo_advisor_runs) if session else "-",
                str(session.tool_calls) if session else "-",
                running,
                idle,
                f"{session.cost:.3f}" if session else "-",
            ]
        )
        if last_action and session and session.last_action and status.stage != "done":
            notes.append((len(rows) - 1, "      last: " + session.last_action[:120]))
    header = ["design", "stage", "iter", "ds", "vitis", "LS", "FA", "calls", "min", "idle_s", "cost$"]
    body = table(rows, header, left={0, 1})
    out = body[:2]
    note_by_row = dict(notes)
    for i, line in enumerate(body[2:]):
        out.append(line)
        if i in note_by_row:
            out.append(note_by_row[i])
    lines += out
    lines += [
        "",
        "  ds = lines in design_space.jsonl; vitis = Vitis launches by the agent (approximate);",
        "  LS / FA = the agent's own LightningSim / FIFOAdvisor runs; calls = agent tool calls.",
        "  min = minutes the agent has worked in this iteration (its total once it has finished);",
        f"  idle_s = seconds since its last event, while working (* = idle > {IDLE_FLAG_SECONDS // 60} min);",
        f"  cost$ = this iteration's agent cost. Agent cost so far in this run: ${total_cost:.2f}.",
    ]
    return lines


def verdict_row(status: IterationStatus, data: dict) -> list[str]:
    baseline = data.get("baseline") or {}
    points = data.get("points") or []
    summary = data.get("summary") or {}
    ls_status = Counter(p.get("lightningsim_status", "n/a") for p in points)
    n_passed = sum(bool(p.get("passed")) for p in points)
    skipped = Counter(
        p.get("lightningsim_skip_reason", "?")
        for p in points
        if p.get("lightningsim_status") == "skipped"
    )
    latencies = [
        p[LATENCY_KEY] for p in points if p.get("passed") and isinstance(p.get(LATENCY_KEY), (int, float))
    ]
    base_latency = baseline.get(LATENCY_KEY)
    speedup = (
        f"{base_latency / min(latencies):.1f}x"
        if latencies and isinstance(base_latency, (int, float)) and base_latency > 0
        else "-"
    )
    baseline_state = baseline.get("lightningsim_status") or ("no baseline" if not baseline else "?")
    problems = [f"{count} {name}" for name, count in ls_status.items() if name not in ("passed",)]
    problems += [f"skip reason: {reason} x{count}" for reason, count in skipped.items()]
    return [
        status.design,
        f"it{status.iteration}",
        baseline_state,
        f"{n_passed}/{len(points)}",
        str(summary.get("n_unique_pareto_points", "-")),
        str(len(summary.get("points_dominating_baseline", []))) if summary else "-",
        speedup,
        "; ".join(problems) if problems else "",
    ]


def report_verdicts(scans: dict[str, dict]) -> list[str]:
    lines = ["HARNESS VERDICTS for finished iterations", ""]
    for run in RUN_DIRS:
        rows = []
        pending = 0
        for case in sorted(scans[run]):
            for iteration in sorted(scans[run][case]):
                status = scans[run][case][iteration]
                if not status.harness_done:
                    continue
                data = load_json(status.path / "iteration_eval_data.json")
                if data is None:
                    pending += 1
                    continue
                rows.append(verdict_row(status, data))
        lines.append(f"  {RUN_TITLES[run]}:")
        if not rows:
            lines.append("    (no finished iterations yet)")
        else:
            header = ["design", "iter", "baseline", "passed", "pareto", "beat_base", "best_speedup", "not passed / notes"]
            lines += ["    " + line for line in table(rows, header, left={0, 1, 2, 7})]
        if pending:
            lines.append(f"    ({pending} file(s) unreadable right now: being written)")
        lines.append("")
    lines += [
        "  baseline = LightningSim outcome of the unmodified design; passed = points that passed every",
        "  stage; pareto = unique Pareto points; beat_base = points dominating the baseline; best_speedup",
        "  = baseline latency / best point latency (LightningSim). Points that did not pass are broken",
        "  down by LightningSim outcome (deadlock / failed / timeout / skipped and why).",
    ]
    return lines


def run_command(args: list[str]) -> str | None:
    try:
        result = subprocess.run(
            args, capture_output=True, text=True, timeout=15, check=False
        )
        return result.stdout.strip() if result.returncode in (0, 1) else None
    except (OSError, subprocess.TimeoutExpired):
        return None


def free_space(path: str) -> str:
    try:
        return f"{shutil.disk_usage(path).free / 2**30:.0f}G"
    except OSError:
        return "?"


SIZE_UNITS = {"B": 1, "kB": 1e3, "MB": 1e6, "GB": 1e9, "TB": 1e12}
# Docker keeps its data on the root filesystem here, so a full root disk breaks the run.
LOW_DISK_GB = 10


def container_layers_gb() -> float | None:
    """Total writable-layer size of the running agent containers (the data they
    have written inside the container, which grows while they work and is freed
    when the iteration ends and the container is removed)."""
    output = run_command(
        ["docker", "ps", "-s", "--filter", f"ancestor={DOCKER_IMAGE}", "--format", "{{.Size}}"]
    )
    if output is None:
        return None
    total = 0.0
    for line in output.splitlines():
        match = re.match(r"([\d.]+)\s*([kMGT]?B)", line.strip())
        if match:
            total += float(match.group(1)) * SIZE_UNITS[match.group(2)]
    return total / 1e9


def report_infrastructure() -> list[str]:
    containers = run_command(["docker", "ps", "-q", "--filter", f"ancestor={DOCKER_IMAGE}"])
    n_containers = len(containers.split()) if containers else 0 if containers is not None else None
    vitis = run_command(["pgrep", "-c", "vitis_hls"])
    lightningsim = run_command(["pgrep", "-fc", "lightningsim /"])
    layers = container_layers_gb()
    warnings = []
    try:
        if shutil.disk_usage("/").free < LOW_DISK_GB * 2**30:
            warnings.append(
                f"  WARNING: less than {LOW_DISK_GB} GB free on / (Docker data lives there): "
                "a full root disk would break the agents."
            )
    except OSError:
        pass
    return [
        "INFRASTRUCTURE",
        "",
        f"  agent containers running: {n_containers if n_containers is not None else 'docker unavailable'}"
        f"   vitis_hls processes (harness + agents): {vitis if vitis is not None else '?'}"
        f"   LightningSim processes (harness + agents): {lightningsim if lightningsim is not None else '?'}",
        f"  free disk: / {free_space('/')}   /usr/scratch {free_space('/usr/scratch')}"
        + (f"   agent container layers: {layers:.1f} GB (on /)" if layers is not None else ""),
        *warnings,
    ]


def build_report(args: argparse.Namespace) -> str:
    now = datetime.now(timezone.utc)
    scans = {run: scan_run(run_dir) for run, run_dir in RUN_DIRS.items()}

    started = [
        status.session.started
        for scan in scans.values()
        for iterations in scan.values()
        for status in iterations.values()
        if status.session and status.session.started
    ]
    if started:
        elapsed = minutes((now - min(started)).total_seconds())
        header = (
            f"Dataflow experiment status, {datetime.now().astimezone():%H:%M:%S %Z on %Y-%m-%d}"
            f"; first agent started {min(started):%H:%M} UTC, {elapsed} min ago"
        )
    else:
        header = f"Dataflow experiment status, {datetime.now().astimezone():%H:%M:%S %Z}; no data yet"

    sections = [[header, "=" * len(header)], report_overview(scans, args.n_iters)]
    for run in RUN_DIRS:
        sections.append(report_run_detail(run, scans[run], now, args.last_action))
    if not args.quick:
        sections.append(report_verdicts(scans))
    sections.append(report_infrastructure())
    return "\n\n".join("\n".join(section) for section in sections)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument(
        "--n-iters",
        type=int,
        default=5,
        help="iterations per design in the experiment (default 5, as in exp_dataflow.py)",
    )
    parser.add_argument("--quick", action="store_true", help="skip the harness verdicts (they parse large files)")
    parser.add_argument("--last-action", action="store_true", help="show each working agent's last command")
    parser.add_argument("--watch", type=float, metavar="SECONDS", help="refresh every SECONDS")
    args = parser.parse_args()

    if not args.watch:
        print(build_report(args))
        return
    try:
        while True:
            if sys.stdout.isatty():
                print("\033[2J\033[H", end="")
            print(build_report(args), flush=True)
            time.sleep(args.watch)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
