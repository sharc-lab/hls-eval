"""Pi evaluation of parameterized dataflow designs, scored with LightningSim.

Like `HLSParameterizationIterativeAgentEvaluatorPi`, but the design's latency
comes from LightningSim (trace + simulate the synthesized design running the
unchanged testbench) instead of the Vitis HLS latency estimate, which can be
inaccurate for dataflow designs. After each agent iteration every point is run
through Vitis HLS synthesis (still the source of the resource metrics) and then
LightningSim, which needs the synthesized solution.

The agent can optionally be given LightningSim and FIFOAdvisor while it works
(`agent_dataflow_tools`). Either way the harness runs LightningSim itself.
"""

from __future__ import annotations

import math
import re
import shutil
import threading
import tomllib
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any

from hls_eval.eval import EvalThreadPools
from hls_eval.eval_agent_pi.eval_agent_pi import run_pi_agent
from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized import (
    PARETO_OBJECTIVES,
    HLSParameterizationIterativeAgentEvaluatorPi,
    _collect_point_artifacts,
    _format_previous_iteration_summary,
    _prompt_section_harness,
    _prompt_section_io,
    _prompt_section_iteration_refinement,
    _prompt_section_optimization,
    _serialize_tool_output,
    _stage_failure_reason,
)
from hls_eval.eval_agent_pi.lightningsim import LightningSimTool
from hls_eval.llms import Model
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool

DATAFLOW_DOCKER_IMAGE_NAME = "hls-eval-agent-pi-dataflow"
DATAFLOW_TOOLS_CONTAINER_DIR = "/opt/hls-dataflow-tools"

LATENCY_KEY = "latency_lightningsim_cycles"
# Same resource objectives as the base evaluator; latency is LightningSim's.
DATAFLOW_OBJECTIVES = (LATENCY_KEY, *PARETO_OBJECTIVES[1:])
DATAFLOW_LATENCY_KEYS = (
    (LATENCY_KEY, "latency (LightningSim)"),
    ("latency_worst_cycles", "Vitis latency estimate"),
)

# Where the two tools come from. With the tools disabled these resolve to
# loopback in the agent container, so the agent cannot install them itself.
BLOCKED_HOSTS = (
    "sharc-lab.github.io",
    "github.com",
    "codeload.github.com",
    "raw.githubusercontent.com",
    "api.github.com",
)

# The synthesis settings the harness uses for every point (`_evaluate_variant`
# runs the synth tool with hls_disable_auto_optimizations and hls_unsafe_math),
# given to the agent so its own solution matches what is measured. A test checks
# these against the Tcl the synthesis tool writes.
HARNESS_SYNTH_CONFIG_TCL = (
    "config_compile -pipeline_loops 0",
    "config_unroll -tripcount_threshold 0",
    "config_array_partition -throughput_driven off",
    "config_compile -unsafe_math_optimizations",
)

# Pixi/conda solution path of the synthesis tool: `<build_dir>/<build name>/...`
SYNTH_BUILD_NAME = "vitis_hls_synth_tool__variant"
SYNTH_SOLUTION_SUBDIR = (
    Path(SYNTH_BUILD_NAME) / f"{SYNTH_BUILD_NAME}__proj" / "solution__synth"
)


def _prompt_section_dataflow_intro() -> str:
    return """You are optimizing a complete, working HLS dataflow design in /workspace.
Read kernel_description.md, the source files, headers and testbench first.
Your goal is to turn the kernel implementation into a Jinja template plus an
explicit set of parameter assignments (design_space.jsonl), so that rendering
each assignment yields a distinct, working hardware implementation. Together
these implementations should trace out a useful latency/resource tradeoff
frontier: some fast and large, some slow and small, and points in between.
The design is (or should become) a task-level pipeline of concurrent processes
connected by streams/FIFOs and ping-pong buffers, so its latency is set by how
well those processes overlap, not just by the latency of each one."""


def _prompt_section_dataflow_guidance() -> str:
    return """Dataflow-specific optimization:
Latency here is the end-to-end execution time of the whole design running the
testbench, measured by cycle-accurate simulation of the synthesized dataflow
(see Evaluation below). It depends on process overlap, on the rate at which
each process produces and consumes data, and on FIFO depths. Consider:
- Balance the initiation intervals and trip counts of producer and consumer
  processes; the slowest process sets the steady-state throughput.
- Choose stream/FIFO depths (`#pragma HLS STREAM variable=<name> depth=<n>`).
  Depths that are too small make processes stall, and can deadlock the design
  (a deadlocked point fails); larger depths cost BRAM/LUT/FF. Depth is a natural
  template parameter.
- Restructure or split processes, replicate them for task-level parallelism, or
  merge them to save resources, wherever functional equivalence is preserved.
- Use `#pragma HLS DATAFLOW` regions, and pipelining, unrolling and array
  partitioning inside each process, as usual."""


def _prompt_section_dataflow_harness(
    *,
    vitis_available: bool,
    dataflow_tools: bool,
    top_function: str,
    tb_file: str,
    tb_data_files: list[str],
    kernel_files: list[str],
    hls_fpga_part: str,
    hls_clock_period_ns: float,
    synth_timeout: float,
    lightningsim_timeout: float,
) -> str:
    tools_note, vitis_note = _prompt_section_harness(vitis_available).split("\n\n", 1)
    if dataflow_tools:
        # Vitis is only a prerequisite here: LightningSim and FIFOAdvisor need the
        # synthesized solution. The generic note would have the agent use Vitis
        # runs (and their latency) to evaluate designs.
        vitis_note = """Vitis HLS (`vitis_hls`) is on PATH, but use it for one thing only: producing
the synthesized solution that LightningSim and FIFOAdvisor read (the recipe
below). Do not use it for anything else: no csim_design or cosim (check
functionality with clang and the testbench), and do not evaluate designs from
its reports. Evaluate designs with LightningSim and FIFOAdvisor. The latency in
a Vitis HLS report can be inaccurate for dataflow designs and is not what the
harness scores. You may read the resource usage in the report of that same run;
it matches the harness's measurement if you use the synthesis settings below.
Do not call Vitis HLS excessively: each synthesis takes minutes, so run it only
when you need a fresh solution for LightningSim or FIFOAdvisor (for a design
variant worth measuring, not after every small edit). You do not need it to find
out how your final designs synthesize: after you finish, the harness synthesizes
every point you submit, and at the start of your next iteration (if there is one)
it gives you the Vitis HLS feedback for each point: whether synthesis passed and
why not if it failed, resource usage, and the synthesis logs, along with the
LightningSim results."""
    elif vitis_available:
        # The generic note promotes the Vitis HLS report's latency, which is not
        # what dataflow designs are scored on.
        vitis_note = """Vitis HLS (`vitis_hls`) is also available on PATH in this environment. You
can run real csynth_design yourself on any rendered point to check whether it
actually synthesizes, and to see its resource usage, before you submit. The
latency in a Vitis HLS report can be inaccurate for dataflow designs and is not
what the harness scores; see Evaluation below, which also gives the per-point
timeouts the harness enforces on csim and csynth."""
    base = tools_note + "\n\n" + vitis_note
    if not dataflow_tools:
        return (
            base
            + """

LightningSim and FIFOAdvisor are NOT available in this environment. After you
submit, the harness synthesizes every point with Vitis HLS and measures its
latency with LightningSim (see Evaluation below). You will not see the results
for the design you are editing now; only the previous iteration's results are
reported to you, if there was one. Reason carefully about stream depths and
process balance rather than relying on the latency estimate in a Vitis HLS
report, which can be inaccurate for dataflow designs."""
        )
    add_files = "\n".join(
        [
            *(f"add_files {name}" for name in kernel_files),
            f"add_files -tb {tb_file}",
            *(f"add_files -tb {name}" for name in tb_data_files),
        ]
    )
    config_tcl = "\n    ".join(HARNESS_SYNTH_CONFIG_TCL)
    return (
        base
        + f"""

LightningSim and FIFOAdvisor are installed and on PATH. They need a Vitis HLS
solution that has been C-synthesized, from a project that registered the
testbench and its data files with `add_files -tb`. For example, a Tcl script run
with `vitis_hls -f run.tcl` (adapt the file list to your rendered sources):
    open_project -reset proj
    {add_files.replace(chr(10), chr(10) + "    ")}
    set_top {top_function}
    open_solution solution1 -flow_target vivado
    set_part {hls_fpga_part}
    create_clock -period {hls_clock_period_ns} -name clk_default
    {config_tcl}
    csynth_design
    exit
The four config_* lines are exactly the settings the harness synthesizes every
point with (Vitis HLS's automatic loop pipelining, unrolling and array
partitioning are off, so only your pragmas and code structure count; unsafe math
is on). Keep them, together with the top function, part and clock above, so that
your solution and its LightningSim/FIFOAdvisor results match what the harness
measures. The solution directory is then `proj/solution1`.
- `lightningsim proj/solution1` traces the testbench and simulates the
  synthesized schedule. It prints the start/end cycle of every module; the top
  module's end cycle is the design's execution latency in cycles, which is the
  latency the harness scores. It exits with status 1 and reports "Deadlock
  detected!" if the FIFO depths make the design deadlock.
- `fifo-advisor proj/solution1 --solver heuristic --output result.json` (other
  options: `--baseline`, `--solver random|group-random|sa|group-sa`,
  `--n-samples N`, `--seed S`, `--maxfun N`) searches FIFO depths for
  latency/BRAM tradeoffs without deadlocks. The output JSON lists each evaluated
  configuration with `fifo_sizes`, `latency`, `bram_usage_total`, `deadlock` and
  ready-made `#pragma HLS STREAM` lines. Only streams that Vitis HLS turned into
  FIFOs are considered. Depths must still be applied by you, in the templates.
- `hls-python` is Python with `lightningsim` and `fifo_advisor` importable, for
  scripting (e.g. `fifo_advisor.opt_env.LSEnv`).
Both tools work only on already-synthesized solutions and take a while per point.

Always give every `vitis_hls`, `lightningsim` and `fifo-advisor` command a
timeout. Your own runs are not limited by the harness, so a command that hangs
blocks you indefinitely. Prefix the command with `timeout <seconds>`, or set the
bash tool's timeout argument. For example:
    timeout {synth_timeout:.0f} vitis_hls -f run.tcl
    timeout {lightningsim_timeout:.0f} lightningsim proj/solution1
Use limits no longer than the harness's own for csynth ({synth_timeout:.0f}s) and
LightningSim ({lightningsim_timeout:.0f}s): a design that needs longer fails in
evaluation anyway, so treat a timeout as a failing point and simplify the design."""
    )


def _prompt_section_dataflow_evaluation(
    hls_fpga_part: str,
    hls_clock_period_ns: float,
    csim_timeout: float,
    synth_timeout: float,
    lightningsim_timeout: float,
    max_points: int,
) -> str:
    return f"""How this will be evaluated after you finish:
Validation renders each point, checks Clang C++ syntax (with
`-Wno-unknown-pragmas`, no `-Werror`) and the original top signature, compiles
and runs the unchanged testbench (csim), and runs Vitis HLS csynth_design for
each rendered point. The target is {hls_fpga_part} with a
{hls_clock_period_ns} ns clock; unsafe math optimizations are enabled and Vitis
HLS's own automatic optimizations (auto-pipelining, auto-unrolling, throughput-
driven array partitioning) are disabled, so any change must come from the
pragmas and code structure you add explicitly. Resource usage (LUT, FF, DSP, BRAM,
URAM) is read from the synthesis report.
Latency is NOT taken from the Vitis HLS report. After synthesis succeeds, the
harness runs LightningSim on the synthesized point: it traces the unchanged
testbench and simulates the dataflow, and the top module's cycle count is the
point's latency. This is why csynth must finish before latency can be known.
A deadlock in that simulation, or a LightningSim failure, scores the point as a
failure with no metrics.
Each point has a {csim_timeout:.0f}s timeout for csim, a separate
{synth_timeout:.0f}s (~{synth_timeout / 60:.1f} min) timeout for csynth_design and a
further {lightningsim_timeout:.0f}s timeout for LightningSim; exceeding any timeout
scores the point as a failure, the same as a compile, runtime, synthesis or
simulation error. The Pareto objectives, all minimized, are LightningSim
latency in cycles and LUT, FF, DSP, BRAM and URAM usage. Missing/unknown metrics
cannot enter the frontier. Failed points remain failures in the evaluation.
Submit at most {max_points} design points in design_space.jsonl. Every point is
synthesized and then simulated with LightningSim, so evaluation time grows with
the number of points; a submission with more than {max_points} points is rejected
as a whole and none of it is evaluated. Prefer a well-chosen spread of distinct
tradeoffs over many similar points.
Validate all points with available tools before finishing. Leave the kernel
templates and design_space.jsonl as the final artifacts; do not replace the
templates with one rendered variant."""


def build_prompt_dataflow(
    kernel_files: list[str],
    top_function: str,
    max_points: int,
    hls_fpga_part: str,
    hls_clock_period_ns: float,
    csim_timeout: float,
    synth_timeout: float,
    lightningsim_timeout: float,
    *,
    tb_file: str,
    tb_data_files: list[str],
    vitis_available: bool,
    dataflow_tools: bool,
    iteration_section: str | None = None,
) -> str:
    sections = [
        iteration_section
        if iteration_section is not None
        else _prompt_section_dataflow_intro(),
        _prompt_section_io(kernel_files, max_points),
        _prompt_section_dataflow_harness(
            vitis_available=vitis_available,
            dataflow_tools=dataflow_tools,
            top_function=top_function,
            tb_file=tb_file,
            tb_data_files=tb_data_files,
            kernel_files=kernel_files,
            hls_fpga_part=hls_fpga_part,
            hls_clock_period_ns=hls_clock_period_ns,
            synth_timeout=synth_timeout,
            lightningsim_timeout=lightningsim_timeout,
        ),
        _prompt_section_optimization(top_function),
        _prompt_section_dataflow_guidance(),
        _prompt_section_dataflow_evaluation(
            hls_fpga_part,
            hls_clock_period_ns,
            csim_timeout,
            synth_timeout,
            lightningsim_timeout,
            max_points,
        ),
    ]
    return "\n\n".join(sections) + "\n"


def _lightningsim_failure_reason(point: dict) -> str | None:
    """Why LightningSim did not produce a latency for a point that reached it."""
    output = point.get("lightningsim_out")
    if point.get("lightningsim_passed") or not output:
        return None
    if (output.get("data_tool") or {}).get("deadlock"):
        return "deadlock detected: the FIFO depths make the dataflow deadlock"
    timeout_or_code = _stage_failure_reason(output)
    if timeout_or_code:
        return timeout_or_code
    error = (output.get("data_tool") or {}).get("parse_error")
    return error or "no latency was reported"


def _lightningsim_stage_text(point: dict) -> str | None:
    status = point.get("lightningsim_status")
    if status is None:
        return None
    if status == "skipped":
        return (
            "lightningsim not run (" + point.get("lightningsim_skip_reason", "") + ")"
        )
    if status == "passed":
        return "lightningsim passed"
    return (
        "lightningsim FAILED (" + (_lightningsim_failure_reason(point) or status) + ")"
    )


def _lightningsim_latency_missing(point: dict) -> str:
    return (
        "LightningSim latency UNDETERMINED ("
        + (_lightningsim_failure_reason(point) or "not available")
        + ")"
    )


def _release_of(path: Path | str | None) -> str | None:
    """The Vitis release (e.g. '2024.1') named by a path, if any."""
    if path is None:
        return None
    for part in reversed(Path(path).parts):
        if re.fullmatch(r"\d{4}\.\d(?:\.\d)?", part):
            return part
    return None


class HLSParameterizationIterativeDataflowAgentEvaluatorPi(
    HLSParameterizationIterativeAgentEvaluatorPi
):
    """Iterative Pi parameterization scored with LightningSim latency.

    `agent_dataflow_tools` selects the agent's environment:
    - True: the agent container has LightningSim and FIFOAdvisor (a Pixi
      environment in the dataflow image) on PATH; requires `vitis_dir`, since
      LightningSim needs the mounted Vitis HLS installation.
    - False: the agent gets neither the tools nor Vitis HLS: `/opt/hls-dataflow-tools`
      is masked by an empty tmpfs so the tools do not exist, their download hosts
      are blocked, and no Vitis installation is mounted (so `vitis_dir`,
      `vivado_dir` and `vitis_license_server` must not be passed). The harness's
      own csim, synthesis and LightningSim runs still use Vitis on the host.
    In both cases the harness runs Vitis HLS synthesis then LightningSim on each
    point (and the baseline) on the host, through the Pixi environment in
    `docker/dataflow_tools`. LightningSim runs on its own thread pool, the same
    size as the synthesis pool, and must use the same Vitis HLS release that
    synthesized the solution: by default `XILINX_HLS` is the synthesis tool's
    installation (override with `lightningsim_xilinx_hls`).
    """

    objectives = DATAFLOW_OBJECTIVES
    eval_type = "hls_parameterization_iterative_dataflow_agentic_pi"

    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        n_iters: int = 3,
        temperature: float = 0.7,
        docker_image_name: str = DATAFLOW_DOCKER_IMAGE_NAME,
        vitis_dir: str | Path | None = None,
        vivado_dir: str | Path | None = None,
        vitis_license_server: str | None = None,
        *,
        agent_dataflow_tools: bool = True,
        lightningsim_timeout: float = 60 * 10,
        lightningsim_xilinx_hls: str | Path | None = None,
        lightningsim_command: Sequence[str] | None = None,
        **kwargs: Any,
    ) -> None:
        if agent_dataflow_tools and vitis_dir is None:
            raise ValueError(
                "agent_dataflow_tools=True requires vitis_dir: LightningSim needs "
                "the Vitis HLS installation mounted in the agent container"
            )
        if not agent_dataflow_tools and any(
            value is not None for value in (vitis_dir, vivado_dir, vitis_license_server)
        ):
            raise ValueError(
                "agent_dataflow_tools=False withholds Vitis HLS from the agent as "
                "well; do not pass vitis_dir, vivado_dir or vitis_license_server"
            )
        if not math.isfinite(lightningsim_timeout) or lightningsim_timeout <= 0:
            raise ValueError("lightningsim_timeout must be positive and finite")
        super().__init__(
            vitis_hls_tool_csim,
            vitis_hls_tool_synth,
            output_data_dir,
            n_samples,
            n_iters,
            temperature,
            docker_image_name,
            vitis_dir,
            vivado_dir,
            vitis_license_server,
            **kwargs,
        )
        self.agent_dataflow_tools = agent_dataflow_tools
        self.lightningsim_timeout = lightningsim_timeout
        self.lightningsim_xilinx_hls = Path(
            lightningsim_xilinx_hls
            if lightningsim_xilinx_hls is not None
            else vitis_hls_tool_synth.vitis_hls_path
        )
        self._check_release_consistency(vitis_hls_tool_synth, vitis_dir)
        self.lightningsim_tool = LightningSimTool(
            self.lightningsim_xilinx_hls, lightningsim_command
        )
        self._ls_pools: dict[int, ThreadPoolExecutor] = {}
        self._ls_pools_lock = threading.Lock()

    def _check_release_consistency(
        self, synth_tool: VitisHLSSynthTool, vitis_dir: str | Path | None
    ) -> None:
        if not (self.lightningsim_xilinx_hls / "include").is_dir():
            raise ValueError(
                f"{self.lightningsim_xilinx_hls} is not a Vitis HLS installation "
                "usable as XILINX_HLS (no include directory)"
            )
        releases = {
            "synthesis tool": _release_of(Path(synth_tool.vitis_hls_path).resolve()),
            "XILINX_HLS for LightningSim": _release_of(
                self.lightningsim_xilinx_hls.resolve()
            ),
            "agent vitis_dir": _release_of(
                Path(vitis_dir).resolve() if vitis_dir is not None else None
            ),
        }
        found = {name: release for name, release in releases.items() if release}
        if len(set(found.values())) > 1:
            raise ValueError(
                "LightningSim must use the Vitis HLS release that synthesizes the "
                f"design, but the releases differ: {found}"
            )

    # ---- LightningSim thread pool -------------------------------------------------

    def _get_lightningsim_pool(self, pools: EvalThreadPools) -> ThreadPoolExecutor:
        """One pool per `EvalThreadPools`, the same size as its synthesis pool.
        The base `EvalThreadPools` has no hook for an extra pool."""
        with self._ls_pools_lock:
            pool = self._ls_pools.get(id(pools))
            if pool is None:
                pool = ThreadPoolExecutor(
                    max_workers=pools.n_jobs_pool_synth,
                    thread_name_prefix="lightningsim",
                )
                self._ls_pools[id(pools)] = pool
            return pool

    def _shutdown_lightningsim_pools(self) -> None:
        with self._ls_pools_lock:
            pools, self._ls_pools = list(self._ls_pools.values()), {}
        for pool in pools:
            pool.shutdown(wait=True)

    def evaluate_designs(self, *args: Any, **kwargs: Any) -> None:
        try:
            super().evaluate_designs(*args, **kwargs)
        finally:
            self._shutdown_lightningsim_pools()

    def evaluate_design_model_pairs(self, *args: Any, **kwargs: Any) -> None:
        try:
            super().evaluate_design_model_pairs(*args, **kwargs)
        finally:
            self._shutdown_lightningsim_pools()

    # ---- Evaluation: synthesis with testbench, then LightningSim -----------------

    @staticmethod
    def _tb_data_names(design_dir: Path) -> list[str]:
        config = design_dir / "hls_eval_config.toml"
        if not config.is_file():
            return []
        return list(tomllib.loads(config.read_text()).get("tb_data", []))

    def _synth_extra_kwargs(self, design_dir: Path, tb_file: str) -> dict[str, Any]:
        # LightningSim re-runs the testbench from the project, so it must be
        # registered (`add_files -tb`) along with its data files.
        tb_files = [design_dir / tb_file]
        tb_files += [
            design_dir / name
            for name in self._tb_data_names(design_dir)
            if (design_dir / name).is_file()
        ]
        return {"tb_files": tb_files}

    def _evaluate_variant(
        self,
        design_dir: Path,
        kernel_files: list[str],
        tb_file: str,
        top_function: str,
        pools: EvalThreadPools,
        expected_signatures: list[dict] | None = None,
    ) -> dict:
        result = super()._evaluate_variant(
            design_dir,
            kernel_files,
            tb_file,
            top_function,
            pools,
            expected_signatures=expected_signatures,
        )
        base_passed = result["passed"]  # everything except LightningSim
        result["lightningsim_passed"] = False
        skipped = [
            reason
            for ok, reason in (
                (result.get("synthesis_passed"), "synthesis failed"),
                (result.get("testbench_passed"), "csim failed"),
                (result.get("interface_preserved"), "interface check failed"),
            )
            if not ok
        ]
        if skipped:
            result["lightningsim_status"] = "skipped"
            result["lightningsim_skip_reason"] = skipped[0]
            result["passed"] = False
            return result

        solution_dir = design_dir.parent / "build" / SYNTH_SOLUTION_SUBDIR
        try:
            output = (
                self._get_lightningsim_pool(pools)
                .submit(
                    self.lightningsim_tool.run,
                    solution_dir,
                    self.lightningsim_timeout,
                    design_dir.parent / "lightningsim.log",
                )
                .result()
            )
        except Exception as error:
            result["lightningsim_status"] = "failed"
            result["lightningsim_error"] = f"{type(error).__name__}: {error}"
            result["passed"] = False
            return result

        result["lightningsim_out"] = _serialize_tool_output(output)
        data = output.data_tool or {}
        latency = data.get(LATENCY_KEY)
        result["lightningsim_passed"] = (
            output.data_execution.return_code == 0
            and not output.data_execution.timeout
            and isinstance(latency, int)
        )
        if result["lightningsim_passed"]:
            result["lightningsim_status"] = "passed"
            result[LATENCY_KEY] = latency
            # Keep the Vitis estimate (`latency_worst_cycles`) beside the
            # LightningSim latency; the Pareto objectives read this dict.
            metrics = (result.get("vitis_hls_tool_out") or {}).get("data_tool")
            if metrics is not None:
                metrics[LATENCY_KEY] = latency
        elif output.data_execution.timeout:
            result["lightningsim_status"] = "timeout"
        elif data.get("deadlock"):
            result["lightningsim_status"] = "deadlock"
        else:
            result["lightningsim_status"] = "failed"
        result["passed"] = base_passed and result["lightningsim_passed"]
        return result

    def _collect_artifacts(
        self, iter_dir: Path, agent_dir: Path, points: list[dict]
    ) -> None:
        _collect_point_artifacts(iter_dir, agent_dir, points)
        for point in points:
            log = (
                iter_dir
                / "points"
                / f"point__{point['point_index']}"
                / "lightningsim.log"
            )
            if point.get("render_success") and log.is_file():
                target = (
                    agent_dir
                    / "previous_design_artifacts"
                    / f"point__{point['point_index']}"
                )
                target.mkdir(parents=True, exist_ok=True)
                shutil.copy(log, target / "lightningsim.log")

    # ---- Prompt and agent environment ---------------------------------------------

    def _build_iteration_prompt(
        self,
        original: Path,
        kernel_files: list[str],
        tb_file: str,
        top_function: str,
        previous_iteration: dict | None,
    ) -> str:
        if previous_iteration is None:
            iteration_section = _prompt_section_dataflow_intro()
        else:
            summary = _format_previous_iteration_summary(
                previous_iteration,
                objectives=self.objectives,
                latency_keys=DATAFLOW_LATENCY_KEYS,
                latency_missing_reason=_lightningsim_latency_missing,
                extra_stage=_lightningsim_stage_text,
                extra_stage_counts=(("lightningsim", "lightningsim_passed"),),
            )
            note = (
                "Latency in this summary is LightningSim's execution latency "
                "(the Vitis HLS estimate is shown only for comparison and is not "
                "scored). previous_design_artifacts/point__<index>/ also holds "
                "lightningsim.log for points that reached LightningSim."
            )
            iteration_section = _prompt_section_iteration_refinement(
                note + "\n\n" + summary
            )
        return build_prompt_dataflow(
            kernel_files,
            top_function,
            self.max_design_points,
            self.hls_fpga_part,
            self.hls_clock_period_ns,
            self.csim_timeout,
            self.synth_timeout,
            self.lightningsim_timeout,
            tb_file=tb_file,
            tb_data_files=self._tb_data_names(original),
            vitis_available=self.vitis_dir is not None,
            dataflow_tools=self.agent_dataflow_tools,
            iteration_section=iteration_section,
        )

    def _agent_container_options(self) -> dict[str, Any]:
        """Tool availability is enforced by the container, not just the prompt."""
        if self.agent_dataflow_tools:
            return {"command_wrappers": ("with-dataflow-tools",)}
        return {
            "tmpfs": {DATAFLOW_TOOLS_CONTAINER_DIR: "size=1m,mode=0755"},
            "extra_hosts": {host: "127.0.0.1" for host in BLOCKED_HOSTS},
        }

    def _run_agent(
        self, agent_dir: Path, prompt: str, model: Model, pools: EvalThreadPools
    ):
        assert model.llm.key is not None  # type: ignore[union-attr]
        return pools.pool_agent.submit(
            run_pi_agent,
            agent_run_dir=agent_dir,
            prompt=prompt,
            model_name=model.llm.model_name,  # type: ignore[union-attr]
            api_key=model.llm.key,  # type: ignore[union-attr]
            docker_image_name=self.docker_image_name,
            vitis_dir=self.vitis_dir,
            vivado_dir=self.vivado_dir,
            vitis_license_server=self.vitis_license_server,
            **self._agent_container_options(),
        ).result()

    def _extra_configuration(self) -> dict[str, Any]:
        return {
            "agent_dataflow_tools": self.agent_dataflow_tools,
            "agent_has_vitis": self.vitis_dir is not None,
            "lightningsim_timeout": self.lightningsim_timeout,
            "lightningsim_xilinx_hls": str(self.lightningsim_xilinx_hls),
            "lightningsim_command": list(self.lightningsim_tool.command),
            "latency_metric": LATENCY_KEY,
        }
