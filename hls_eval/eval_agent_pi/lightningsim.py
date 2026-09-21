"""Run LightningSim on a synthesized Vitis HLS solution and parse its latency.

LightningSim traces the design's testbench against the C-synthesis schedule, so
its solution directory must come from a csynth run whose project registered the
testbench (`add_files -tb`); see `VitisHLSSynthTool.run(tb_files=...)`.
"""

from __future__ import annotations

import os
import re
import subprocess
import time
from collections.abc import Sequence
from pathlib import Path

import psutil

from hls_eval.tools import ExecutionData, ToolDataOutput

DATAFLOW_TOOLS_DIR = Path(__file__).resolve().parent / "docker" / "dataflow_tools"

# The top module is the first, unindented line of LightningSim's module tree:
#   [      0-1597077] forward
_TOP_MODULE_RE = re.compile(r"^\[\s*(\d+)\s*-\s*(\d+)\]\s+(\S+)\s*$", re.MULTILINE)


def default_lightningsim_command() -> tuple[str, ...]:
    """Run the CLI from the repo's Pixi environment (activation sets CC/CXX)."""
    return (
        "pixi",
        "run",
        "--frozen",
        "--manifest-path",
        str(DATAFLOW_TOOLS_DIR / "pixi.toml"),
        "lightningsim",
    )


def parse_lightningsim_output(output: str) -> dict:
    """Return the top module's latency, or a dict with `deadlock`/`parse_error`."""
    if "Deadlock detected" in output:
        return {"latency_lightningsim_cycles": None, "deadlock": True}
    match = _TOP_MODULE_RE.search(output)
    if match is None:
        return {
            "latency_lightningsim_cycles": None,
            "deadlock": False,
            "parse_error": "no top-module line found in LightningSim output",
        }
    start, end, name = int(match.group(1)), int(match.group(2)), match.group(3)
    return {
        "latency_lightningsim_cycles": end - start,
        "deadlock": False,
        "top_module": name,
        "top_module_start_cycle": start,
        "top_module_end_cycle": end,
    }


def _tree_rss_bytes(process: psutil.Process) -> int:
    total = 0
    try:
        procs = [process, *process.children(recursive=True)]
    except psutil.Error:
        return 0
    for proc in procs:
        try:
            total += proc.memory_info().rss
        except psutil.Error:
            pass
    return total


def _kill_tree(process: psutil.Process) -> None:
    try:
        procs = [*process.children(recursive=True), process]
    except psutil.Error:
        procs = [process]
    for proc in procs:
        try:
            proc.kill()
        except psutil.Error:
            pass


class LightningSimTool:
    """Trace and simulate a synthesized solution, returning `ToolDataOutput`.

    `xilinx_hls` must be the same Vitis HLS release that produced the solution:
    LightningSim reads the solution's bitcode and compiles the testbench against
    that release's headers (`$XILINX_HLS/include`).
    """

    def __init__(
        self,
        xilinx_hls: Path,
        command: Sequence[str] | None = None,
        poll_interval: float = 0.5,
    ) -> None:
        self.xilinx_hls = Path(xilinx_hls)
        self.command = tuple(command) if command else default_lightningsim_command()
        self.poll_interval = poll_interval

    def run(
        self,
        solution_dir: Path,
        timeout: float = 60.0 * 10,
        log_path: Path | None = None,
    ) -> ToolDataOutput:
        solution_dir = Path(solution_dir).resolve()
        log_path = log_path or solution_dir.parent / "lightningsim.log"
        env = {**os.environ, "XILINX_HLS": str(self.xilinx_hls)}

        t_0 = time.monotonic()
        peak_rss = 0
        timed_out = False
        try:
            with log_path.open("w") as log:
                p = subprocess.Popen(
                    [*self.command, str(solution_dir)],
                    cwd=solution_dir,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    env=env,
                )
                process = psutil.Process(p.pid)
                while True:
                    try:
                        p.wait(timeout=self.poll_interval)
                        break
                    except subprocess.TimeoutExpired:
                        peak_rss = max(peak_rss, _tree_rss_bytes(process))
                        if time.monotonic() - t_0 > timeout:
                            timed_out = True
                            _kill_tree(process)
                            p.wait()
                            break
        except OSError as error:
            t_1 = time.monotonic()
            return ToolDataOutput(
                ExecutionData(-1, "", str(error), t_0, t_1, t_1 - t_0, False), None
            )

        t_1 = time.monotonic()
        output = log_path.read_text(errors="replace")
        execution = ExecutionData(
            return_code=-1 if timed_out else p.returncode,
            stdout=output,
            stderr="",
            t0=t_0,
            t1=t_1,
            execution_time=timeout if timed_out else t_1 - t_0,
            timeout=timed_out,
        )
        if timed_out or p.returncode not in (0, 1):
            return ToolDataOutput(execution, None)

        data = parse_lightningsim_output(output)
        if p.returncode == 1 and not data.get("deadlock"):
            # A nonzero exit that is not a reported deadlock is a plain failure.
            return ToolDataOutput(execution, None)
        data["peak_rss_mb"] = peak_rss / 2**20
        return ToolDataOutput(execution, data)
