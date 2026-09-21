`HLSParameterizationAgentEvaluatorPi` gives Pi a complete benchmark and asks it to
edit the existing kernel implementations into Jinja templates and create an
explicit `design_space.jsonl`.

```python
from pathlib import Path

from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized import (
    HLSParameterizationAgentEvaluatorPi,
)
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool

vitis = Path("/tools/software/xilinx/ARCHIVE/Vitis_HLS/2024.1")
evaluator = HLSParameterizationAgentEvaluatorPi(
    vitis_hls_tool_csim=VitisHLSCSimTool(vitis),
    vitis_hls_tool_synth=VitisHLSSynthTool(vitis),
    output_data_dir=Path("output_parameterization"),
    vitis_dir=vitis,
    clang_bin="clang++",
    max_design_points=64,
    hls_fpga_part="xczu9eg-ffvb1156-2-e",
    hls_clock_period_ns=5,
    compile_timeout=60,
    csim_timeout=120,
    synth_timeout=360,
)
evaluator.evaluate_designs(
    benchmark_cases=benchmark_cases,
    models=models,  # OpenRouter models, as for the generation Pi evaluator
    n_jobs_pool_agent=1,
    n_jobs_pool_csim=2,
    n_jobs_pool_synth=2,
)
```

The host needs a Clang version supporting JSON AST dumps, the project Python
dependencies, and a working Vitis HLS installation providing both C-simulation
and synthesis. The existing Pi Docker image and optional Vitis/Vivado/license
mounts are reused. `clang_flags` adds compiler options; `compile_timeout` bounds
the Clang syntax/signature check, `csim_timeout` bounds the Vitis HLS C-simulation
compile-and-run step, and `synth_timeout` bounds synthesis. Native Clang is used
only for the static interface-signature check described below, since Vitis HLS
has no equivalent for it; compiling and executing the testbench goes through the
supplied `VitisHLSCSimTool` (the same Csim flow every other evaluator in this
project uses), and synthesis goes through the supplied `VitisHLSSynthTool` (the
same Csynth flow). As with every other evaluator, test data files referenced from
`hls_eval_config.toml`'s `tb_data` must be flat filenames, not nested paths: the
underlying tools copy them by basename into the build directory. The inherited
`temperature` argument is accepted for compatibility; the current Pi runner does
not forward a temperature setting.

Each nonblank JSONL line must be a distinct object of scalar parameters, for
example:

```jsonl
{"unroll_factor": 1, "pipeline": false}
{"unroll_factor": 2, "pipeline": true}
{"unroll_factor": 4, "pipeline": true}
```

There must be 2 to `max_design_points` assignments, producing at least two distinct
rendered implementations. Empty, malformed, oversized or duplicate assignment
lists fail submission validation. Missing template variables fail the affected
point. All points are evaluated; failures are retained rather than silently
removed. Scratch files created by the agent are excluded from validation: only
original benchmark files and the rendered existing kernels enter each build.

The checks are:

- Compare every original non-kernel file byte for byte, including all headers,
  the testbench, configuration and test data. Deletion also fails the submission.
- Render each point through `JinjaParamaterizationFlow` with strict undefined
  variables; require no remaining Jinja delimiters.
- Check kernel syntax with Clang and compare the top function's definition,
  C++ type, linkage and storage class against the original. Explicit
  `#pragma HLS INTERFACE` directives in the kernels must also remain unchanged.
- Compile the kernel translation units and headers with the original testbench
  and execute it via Vitis HLS `csim_design`, requiring exit code zero within
  the timeout.
- Run Vitis `csynth_design` using the original top name, with fixed part/clock
  settings, unsafe math optimizations enabled, and Vitis HLS's own automatic
  optimizations (auto-pipelining, auto-unrolling, throughput-driven array
  partitioning) disabled, so latency/resource differences come from the
  agent's own pragmas rather than the tool's defaults. Synthesis is attempted
  even for a rendered point whose C++ or functional checks fail.

Every check runs independently per point (and for the baseline), so a Clang,
C-simulation or synthesis failure on one point never blocks the others. Results
are logged with the same `c_compile_out`/`c_run_out`/`vitis_hls_tool_out` shape
(`data_execution` plus `data_tool`) used by every other evaluator in this
project.

These checks establish interface compatibility and correctness over the supplied
testbench inputs; they are not a proof of functional equivalence for every input
or RTL equivalence. The directive comparison covers explicit source pragmas,
not arbitrary macro-generated port directives.

Each sample stores the original design, agent workspace, prompt and Pi trace,
`design_space.jsonl`, an independently compiled/synthesized `baseline`, and
`points/point__N/design` plus `result.json` for every assignment. The sample's
`single_eval_data.json` contains all checks and tool diagnostics, and
`all_eval_data.json` combines samples. Agent failures are recorded without
aborting later samples.

`summary` minimizes worst-case latency in cycles, LUTs, FFs, DSPs, BRAMs and URAMs
jointly. Only points passing every correctness/synthesis check with all six finite,
nonnegative metrics are eligible. Unknown latency is not replaced with zero or
best-case latency. The summary records nondominated point indices, distinct
objective vectors, the unique frontier fraction over **all submitted points**,
and which points dominate or are dominated by the original baseline. Equal
objective vectors count once toward diversity. All raw synthesis metrics are
retained. Correctness `passed` is separate from optimization quality: there is
no arbitrary scalar quality score or claim that the measured frontier is globally
optimal. Frontier size, coverage and baseline comparisons should be considered
together when assessing the agent's optimization quality.

## Dataflow evaluator: `HLSParameterizationIterativeDataflowAgentEvaluatorPi`

Defined in `eval_agent_pi_paramaterized_dataflow.py`. It follows
`HLSParameterizationIterativeAgentEvaluatorPi` with a dataflow-specific prompt and
an image with LightningSim and FIFOAdvisor (see `docker/README.md`).

```python
evaluator = HLSParameterizationIterativeDataflowAgentEvaluatorPi(
    vitis_hls_tool_csim=VitisHLSCSimTool(vitis),
    vitis_hls_tool_synth=VitisHLSSynthTool(vitis),
    output_data_dir=Path("output_dataflow"),
    n_iters=3,
    vitis_dir=vitis,                  # required when agent_dataflow_tools=True
    agent_dataflow_tools=True,        # False: no tools and no Vitis for the agent
                                      # (vitis_dir must then be None)
    lightningsim_timeout=600,
)
evaluator.evaluate_designs(
    benchmark_cases, models, n_jobs_pool_agent=8, n_jobs_pool_csim=16, n_jobs_pool_synth=16
)
```

Per point, after each agent iteration: Clang interface check and csim, then Vitis
HLS synthesis (with the testbench registered via `add_files -tb`), then
LightningSim on the synthesized solution. Resource metrics come from the
synthesis report; **latency is LightningSim's top-module cycle count**
(`latency_lightningsim_cycles`), which replaces `latency_worst_cycles` in the
Pareto objectives. The Vitis estimate is kept beside it for comparison. A point
passes only if LightningSim reports a latency.

- LightningSim runs on its own thread pool, the same size as `n_jobs_pool_synth`,
  on the host through the Pixi environment in `docker/dataflow_tools`. Each run
  uses about 1.5 GB of memory on `atax`; peak RSS is recorded per run.
- Its `XILINX_HLS` defaults to the synthesis tool's installation (override with
  `lightningsim_xilinx_hls`); a mismatch of releases between the synthesis tool,
  that path and `vitis_dir` is rejected. Use the Vitis HLS release LightningSim
  works with (2024.1 was validated; see `docker/README.md`).
- Failures are kept per point: `lightningsim_status` is `passed`, `deadlock`,
  `timeout`, `failed` or `skipped` (with `lightningsim_skip_reason`, when
  synthesis or csim failed). They are reported to the next iteration's agent
  along with `lightningsim.log`.
- Access mode is enforced by the container, not just by the prompt, which also
  changes. With the tools on, they and Vitis HLS are present and on `PATH`. With
  them off, the tools are absent and not installable and no Vitis HLS is mounted
  for the agent, so it can only check its work with clang and the testbench.
