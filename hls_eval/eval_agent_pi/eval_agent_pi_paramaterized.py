"""Pi evaluation of complete kernels parameterized with Jinja and explicit JSONL."""

from __future__ import annotations

import hashlib
import json
import math
import re
import shutil
import subprocess
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, cast

from llm_openrouter import OpenRouterChat

from hls_eval.data import CPP_EXTENSIONS, H_EXTENSIONS, BenchmarkCase
from hls_eval.eval import EvalThreadPools, serialize_eval_data
from hls_eval.eval_agent_pi.eval_agent_pi import (
    DOCKER_IMAGE_NAME,
    HLSGenerationAgentEvaluatorPi,
    run_pi_agent,
)
from hls_eval.flow_parameterization.flow_parameterization import (
    DesignSpaceExplicit,
    JinjaParamaterizationFlow,
)
from hls_eval.llms import Model, normalize_model_name
from hls_eval.tools import (
    ExecutionData,
    ToolDataOutput,
    VitisHLSCSimTool,
    VitisHLSSynthTool,
)

PARETO_OBJECTIVES = (
    "latency_worst_cycles",
    "resources_lut_used",
    "resources_ff_used",
    "resources_dsp_used",
    "resources_bram_used",
    "resources_uram_used",
)


def _prompt_section_intro() -> str:
    return """You are optimizing a complete, working HLS design in /workspace.
Read kernel_description.md, the source files, headers and testbench first.
Your goal is to turn the kernel implementation into a Jinja template plus an
explicit set of parameter assignments (design_space.jsonl), so that rendering
each assignment yields a distinct, working hardware implementation. Together
these implementations should trace out a useful latency/resource tradeoff
frontier: some fast and large, some slow and small, and points in between."""


def _prompt_section_io(kernel_files: list[str], max_points: int) -> str:
    return f"""Input / output file layout:
Modify only these existing kernel implementation files: {json.dumps(kernel_files)}.
Create design_space.jsonl in /workspace. Preserve all other original files byte
for byte, including every header, the testbench, input data and configuration.
Do not parameterize headers or the testbench. Scratch files may be created but
are not included in the submitted design.

Parameterize the kernel implementations using Jinja syntax: {{{{ factor }}}} for
values and {{% if pipeline %}} ... {{% endif %}} for conditional code. Each
nonblank line of design_space.jsonl must be one JSON object containing a
complete, explicit parameter assignment. Use string keys and finite
string/number/boolean values, no arrays, nulls or nested objects. Submit
between 2 and {max_points} distinct assignments, yielding at least two distinct
fully rendered implementations. This is an explicit list of points, not a
schema, ranges or a Cartesian-product specification. Every line is evaluated.
For example, two lines might be:
{{"unroll_factor": 1, "pipeline": false}}
{{"unroll_factor": 4, "pipeline": true}}
Every template variable must have a value; missing variables fail rendering.

Validation strictly re-renders every point and fails it if the rendered source
still contains a literal {{{{, {{%, or {{# anywhere, even inside a {{% raw %}}
block. If your original C/C++ contains literal double braces (e.g. a nested
array or struct initializer like {{{{0,1,2}}, {{3,4,5}}}}), do not rely on
{{% raw %}} to protect it: wrapping it in raw only reproduces those literal
braces verbatim, which still fails validation. Instead, either reformat the
literal so no {{{{ substring appears in the rendered output (e.g. add a space:
{{ {{0,1,2}}, {{3,4,5}} }}), or emit the brace explicitly with a Jinja expression,
e.g. {{{{ '{{' }}}} renders to a single literal {{ character before validation
ever sees it."""


def _prompt_section_harness(vitis_available: bool) -> str:
    tools = """Environment and tools available in /workspace:
clang/clang++ and a standard build toolchain are installed for syntax checks
and compiling/running the testbench yourself before submitting. `uv` is also
preinstalled for any Python tooling you want: run one-off scripts with
`uv run --with <package> script.py`, or set up a full environment with
`uv venv` and `uv add <packages>`. Use it freely for automating checks,
analysis, or modeling, not just template rendering (e.g. installing jinja2 to
render and inspect your own templates before submitting)."""
    if vitis_available:
        vitis_note = """Vitis HLS (`vitis_hls`) is also available on PATH in this environment. You
can run real csynth_design yourself on any rendered point to check whether it
actually synthesizes, and to see its real latency/resource numbers, before
you submit. Use this to catch synthesis-only failures and pathological
pragma combinations (e.g. ones that make synthesis hang or take a very long
time) that clang and the testbench alone cannot reveal."""
    else:
        vitis_note = """Vitis HLS is NOT available in this environment, so you cannot run
csynth_design yourself. Self-validate only with clang syntax checks and by
compiling/running the unchanged testbench; real synthesis is validated
automatically by the harness after you submit (see Evaluation below), and you
will not see those results. Because of this blind spot, avoid speculative or
extreme pragma combinations you cannot reason about confidently (e.g. very
large unroll/partition factors stacked together): they are more likely to
time out or produce unbounded/unreported latency during the harness's real
synthesis, which silently removes that point from the Pareto frontier."""
    return tools + "\n\n" + vitis_note


def _prompt_section_optimization(top_function: str) -> str:
    return f"""How to parameterize and optimize the design:
You are not required to keep the original implementation's structure, for
either the algorithm or its hardware architecture. You may restructure loops,
change data flow, reorganize storage, or use a different algorithm entirely,
as long as every rendered point stays functionally equivalent at the top-level
interface: identical outputs for all valid inputs.

The parameterization itself can be as complex as it needs to be: it does not
have to be limited to toggling pragma values or factors on an otherwise fixed
code skeleton. `{{% if %}}` blocks can select between substantially different
code structures per point, including a different architecture from the
baseline implementation, if that is what a given point's tradeoff needs.

Seek many useful latency/resource tradeoffs through loop unrolling, pipelining,
array partitioning/reshaping, storage binding and resource allocation, and
through functionally equivalent algorithmic or architectural restructuring
shared across the design space. Choose legal factors and compatible
combinations. Aim for most submitted points to be distinct, nondominated
hardware tradeoffs and improve the entire frontier, including its fast and
small endpoints, relative to the original design. Duplicate renderings or
identical measured outcomes do not add tradeoff diversity. The baseline,
unparameterized design is itself measured as a reference point. The goal is
for the baseline to never end up as the sole point on the Pareto front: it
should either be dominated by at least one of your points, or sit on the
frontier alongside several of your points, not stand alone as the only
nondominated tradeoff.

Preserve the exact top function {top_function!r}, its linkage, parameter and return
types, port/interface pragmas and behavior for all valid inputs at EVERY point.
Do not change dimensions, numerical precision, arithmetic semantics or output
values to obtain a speedup. Do not bypass the testbench or specialize on its data.
Do not use simulation/synthesis conditionals to implement different behavior."""


def _prompt_section_evaluation(hls_fpga_part: str, hls_clock_period_ns: float) -> str:
    return f"""How this will be evaluated after you finish:
Validation renders each point, checks Clang C++ syntax (with
`-Wno-unknown-pragmas`, no `-Werror`, so HLS pragmas and unused helper code do
not themselves cause syntax failures) and the original top signature, compiles
and runs the unchanged testbench, and runs Vitis HLS csynth_design for each
rendered point. The target is {hls_fpga_part} with a
{hls_clock_period_ns} ns clock; unsafe math optimizations are enabled and Vitis
HLS's own automatic optimizations (auto-pipelining, auto-unrolling, throughput-
driven array partitioning) are disabled, so any latency/resource change must
come from the pragmas and code structure you add explicitly. The Pareto
objectives, all minimized, are worst-case latency in cycles and LUT, FF, DSP,
BRAM and URAM usage. Missing/unknown metrics cannot enter the frontier. Failed
points remain failures in the evaluation. Validate all points with available tools
before finishing. Leave the kernel templates and design_space.jsonl as the final
artifacts; do not replace the templates with one rendered variant."""


def build_prompt_parameterization(
    kernel_files: list[str],
    top_function: str,
    max_points: int,
    hls_fpga_part: str,
    hls_clock_period_ns: float,
    *,
    vitis_available: bool = False,
) -> str:
    sections = [
        _prompt_section_intro(),
        _prompt_section_io(kernel_files, max_points),
        _prompt_section_harness(vitis_available),
        _prompt_section_optimization(top_function),
        _prompt_section_evaluation(hls_fpga_part, hls_clock_period_ns),
    ]
    return "\n\n".join(sections) + "\n"


def _succeeded(output: ToolDataOutput | None) -> bool:
    return output is not None and (
        output.data_execution.return_code == 0 and not output.data_execution.timeout
    )


def _serialize_tool_output(tool_output: ToolDataOutput) -> dict[str, Any]:
    return {
        "data_execution": {
            "return_code": tool_output.data_execution.return_code,
            "stdout": tool_output.data_execution.stdout,
            "stderr": tool_output.data_execution.stderr,
            "t0": tool_output.data_execution.t0,
            "t1": tool_output.data_execution.t1,
            "execution_time": tool_output.data_execution.execution_time,
            "timeout": tool_output.data_execution.timeout,
        },
        "data_tool": tool_output.data_tool or {},
    }


def _interface_pragmas(sources: dict[str, str]) -> dict[str, list[str]]:
    """Keep explicit HLS port directives fixed in addition to the C++ signature."""
    return {
        name: sorted(
            " ".join(match.split())
            for match in re.findall(
                r"(?mi)^\s*#\s*pragma\s+HLS\s+INTERFACE\b([^\n]*)",
                source.replace("\\\n", ""),
            )
        )
        for name, source in sources.items()
    }


def _run_command(command: list[str], cwd: Path, timeout: float) -> ToolDataOutput:
    start = time.monotonic()
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        code, stdout, stderr, timed_out = (
            result.returncode,
            result.stdout,
            result.stderr,
            False,
        )
    except subprocess.TimeoutExpired as error:

        def decode(value):
            return (
                value.decode(errors="replace")
                if isinstance(value, bytes)
                else value or ""
            )

        code, stdout, stderr, timed_out = (
            -1,
            decode(error.stdout),
            decode(error.stderr),
            True,
        )
    except OSError as error:
        code, stdout, stderr, timed_out = -1, "", str(error), False
    end = time.monotonic()
    return ToolDataOutput(
        ExecutionData(code, stdout, stderr, start, end, end - start, timed_out),
        None,
    )


def _top_signatures(ast_output: str, top_function: str) -> list[dict]:
    """Clang's filtered AST can contain several consecutive JSON documents."""
    decoder = json.JSONDecoder()
    signatures = []
    remaining = ast_output.lstrip()
    while remaining:
        node, end = decoder.raw_decode(remaining)
        remaining = remaining[end:].lstrip()
        if (
            node.get("kind") == "FunctionDecl"
            and node.get("name") == top_function
            and any(
                child.get("kind") == "CompoundStmt" for child in node.get("inner", [])
            )
        ):
            signatures.append(
                {
                    "type": node["type"]["qualType"],
                    "mangled_name": node.get("mangledName"),
                    "storage_class": node.get("storageClass"),
                }
            )
    return sorted(
        signatures, key=lambda signature: json.dumps(signature, sort_keys=True)
    )


def _objective_values(point: dict) -> tuple[float, ...] | None:
    if not point.get("passed"):
        return None
    metrics = point.get("vitis_hls_tool_out", {}).get("data_tool") or {}
    values = tuple(metrics.get(key) for key in PARETO_OBJECTIVES)
    if not all(
        isinstance(value, (int, float))
        and not isinstance(value, bool)
        and math.isfinite(value)
        and value >= 0
        for value in values
    ):
        return None
    return cast(tuple[float, ...], values)


def _dominates(left: tuple, right: tuple) -> bool:
    return all(a <= b for a, b in zip(left, right, strict=True)) and any(
        a < b for a, b in zip(left, right, strict=True)
    )


def summarize_design_space(points: list[dict], baseline: dict) -> dict:
    eligible = [
        (point["point_index"], values)
        for point in points
        if (values := _objective_values(point)) is not None
    ]
    frontier = [
        (index, values)
        for index, values in eligible
        if not any(_dominates(other, values) for _, other in eligible)
    ]
    # Equal objective vectors are nondominated, but only count once as a tradeoff.
    unique_frontier: dict[tuple[float, ...], int] = {}
    for index, values in frontier:
        unique_frontier.setdefault(values, index)
    baseline_values = _objective_values(baseline)
    total = len(points)
    return {
        "objectives": list(PARETO_OBJECTIVES),
        "objective_direction": "minimize",
        "n_points": total,
        "n_rendered": sum(p.get("render_success", False) for p in points),
        "n_unique_renderings": len(
            {p["source_sha256"] for p in points if "source_sha256" in p}
        ),
        "n_passed": sum(p.get("passed", False) for p in points),
        "n_metric_eligible": len(eligible),
        "pareto_point_indices": [index for index, _ in frontier],
        "unique_pareto_point_indices": list(unique_frontier.values()),
        "n_unique_pareto_points": len(unique_frontier),
        "unique_pareto_fraction": len(unique_frontier) / total if total else 0.0,
        "baseline_objectives": dict(zip(PARETO_OBJECTIVES, baseline_values))
        if baseline_values
        else None,
        "points_dominating_baseline": [
            index for index, values in eligible if _dominates(values, baseline_values)
        ]
        if baseline_values
        else [],
        "points_dominated_by_baseline": [
            index for index, values in eligible if _dominates(baseline_values, values)
        ]
        if baseline_values
        else [],
    }


class HLSParameterizationAgentEvaluatorPi(HLSGenerationAgentEvaluatorPi):
    """Evaluate Jinja kernel templates against an untouched complete benchmark.

    Native Clang performs only the static syntax/ABI interface-signature check
    (the vendor Vitis HLS toolchain has no equivalent). Compiling and executing
    the testbench goes through the supplied `VitisHLSCSimTool` (the same Csim
    flow every other evaluator uses), and synthesis goes through the supplied
    `VitisHLSSynthTool` (the same Csynth flow). Each point and the baseline
    retain independent results, logged in the same `data_execution`/`data_tool`
    shape used by the rest of the codebase.
    """

    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        temperature: float = 0.7,
        docker_image_name: str = DOCKER_IMAGE_NAME,
        vitis_dir: str | Path | None = None,
        vivado_dir: str | Path | None = None,
        vitis_license_server: str | None = None,
        *,
        clang_bin: str | Path = "clang++",
        clang_flags: tuple[str, ...] = (),
        max_design_points: int = 8,
        compile_timeout: float = 120,
        csim_timeout: float = 120,
        synth_timeout: float = 60 * 8,
        hls_fpga_part: str = "xczu9eg-ffvb1156-2-e",
        hls_clock_period_ns: float = 5,
    ) -> None:
        if n_samples < 1 or max_design_points < 2:
            raise ValueError(
                "n_samples must be positive and max_design_points must be >= 2"
            )
        if any(
            not math.isfinite(t) or t <= 0
            for t in (
                compile_timeout,
                csim_timeout,
                synth_timeout,
                hls_clock_period_ns,
            )
        ):
            raise ValueError("Timeouts and clock period must be positive and finite")
        super().__init__(
            vitis_hls_tool_csim,
            vitis_hls_tool_synth,
            output_data_dir,
            n_samples,
            temperature,
            docker_image_name,
            vitis_dir,
            vivado_dir,
            vitis_license_server,
        )
        self.clang_bin = str(clang_bin)
        self.clang_flags = clang_flags
        self.max_design_points = max_design_points
        self.compile_timeout = compile_timeout
        self.csim_timeout = csim_timeout
        self.synth_timeout = synth_timeout
        self.hls_fpga_part = hls_fpga_part
        self.hls_clock_period_ns = hls_clock_period_ns

    def _check_interface_signature(
        self, design_dir: Path, kernel_files: list[str], top_function: str
    ) -> dict:
        """Static, source-only check: no Vitis HLS equivalent exists for this."""
        includes = Path(self.cpp_compiler_tool.vitis_hls_path).resolve() / "include"
        sources = [str(design_dir / name) for name in kernel_files]
        syntax = _run_command(
            [
                self.clang_bin,
                "-std=c++14",
                "-Wno-unknown-pragmas",
                f"-I{design_dir}",
                f"-I{includes}",
                f"-I{includes / 'etc'}",
                f"-I{includes / 'utils'}",
                *self.clang_flags,
                "-fsyntax-only",
                "-Xclang",
                "-ast-dump=json",
                "-Xclang",
                f"-ast-dump-filter={top_function}",
                *sources,
            ],
            design_dir,
            self.compile_timeout,
        )
        result: dict[str, Any] = {
            "clang_syntax_out": _serialize_tool_output(syntax),
            "clang_syntax_passed": _succeeded(syntax),
            "top_signatures": [],
        }
        if result["clang_syntax_passed"]:
            try:
                result["top_signatures"] = _top_signatures(
                    syntax.data_execution.stdout, top_function
                )
            except (ValueError, KeyError, TypeError) as error:
                result["interface_error"] = str(error)
        return result

    def _evaluate_variant(
        self,
        design_dir: Path,
        kernel_files: list[str],
        tb_file: str,
        top_function: str,
        pools: EvalThreadPools,
        expected_signatures: list[dict] | None = None,
    ) -> dict:
        result: dict[str, Any] = {"passed": False}
        interface_future = pools.pool_csim.submit(
            self._check_interface_signature, design_dir, kernel_files, top_function
        )

        # Use only trusted headers and rendered implementations for synthesis.
        header_files = sorted(
            p for p in design_dir.rglob("*") if p.suffix in H_EXTENSIONS and p.is_file()
        )
        kernel_and_headers = sorted(
            set(design_dir / name for name in kernel_files) | set(header_files)
        )
        tb_path = design_dir / tb_file
        csim_sources = sorted(set(kernel_and_headers) | {tb_path})
        csim_aux = sorted(
            p for p in design_dir.rglob("*") if p.is_file() and p not in csim_sources
        )
        build_dir = design_dir.parent / "build"
        csim_future = pools.pool_csim.submit(
            self.cpp_compiler_tool.run,
            build_dir,
            csim_sources,
            csim_aux,
            build_name="variant",
            hls_top_function=top_function,
            hls_fpga_part=self.hls_fpga_part,
            hls_clock_period_ns=self.hls_clock_period_ns,
            timeout=self.csim_timeout,
        )
        synth_future = pools.pool_synth.submit(
            self.vitis_hls_tool.run,
            build_dir,
            kernel_and_headers,
            build_name="variant",
            hls_top_function=top_function,
            hls_fpga_part=self.hls_fpga_part,
            hls_clock_period_ns=self.hls_clock_period_ns,
            hls_unsafe_math=True,
            hls_disable_auto_optimizations=True,
            timeout=self.synth_timeout,
        )

        try:
            result.update(interface_future.result())
        except Exception as error:
            result["interface_error"] = f"{type(error).__name__}: {error}"

        try:
            compile_out, run_out = csim_future.result()
            result["c_compile_out"] = _serialize_tool_output(compile_out)
            result["compile_passed"] = _succeeded(compile_out)
            result["testbench_passed"] = False
            if run_out is not None:
                result["c_run_out"] = _serialize_tool_output(run_out)
                result["testbench_passed"] = _succeeded(run_out)
        except Exception as error:
            result["compile_passed"] = False
            result["testbench_passed"] = False
            result["csim_error"] = f"{type(error).__name__}: {error}"

        try:
            synthesis = synth_future.result()
            result["vitis_hls_tool_out"] = _serialize_tool_output(synthesis)
            result["synthesis_passed"] = _succeeded(synthesis)
        except Exception as error:
            result["synthesis_passed"] = False
            result["synthesis_error"] = f"{type(error).__name__}: {error}"

        signatures = result.get("top_signatures", [])
        result["interface_preserved"] = bool(signatures) and (
            len(signatures) == 1
            if expected_signatures is None
            else signatures == expected_signatures
        )
        result["passed"] = all(
            result.get(key, False)
            for key in (
                "clang_syntax_passed",
                "compile_passed",
                "testbench_passed",
                "interface_preserved",
                "synthesis_passed",
            )
        )
        return result

    def _read_submission(
        self, original: Path, submitted: Path, kernel_files: list[str], tb_file: str
    ) -> tuple[dict, dict[str, str], DesignSpaceExplicit]:
        modified = []
        for source in sorted(original.rglob("*")):
            if not source.is_file():
                continue
            relative = source.relative_to(original)
            if (
                relative.as_posix() in kernel_files
                or relative.as_posix() == "design_space.jsonl"
            ):
                continue
            candidate = submitted / relative
            if (
                candidate.is_symlink()
                or not candidate.is_file()
                or not candidate.resolve().is_relative_to(submitted.resolve())
                or candidate.read_bytes() != source.read_bytes()
            ):
                modified.append(relative.as_posix())
        checks = {
            "modified_protected_files": modified,
            "has_modified_testbench": tb_file in modified,
            "has_modified_header": any(
                Path(name).suffix in H_EXTENSIONS for name in modified
            ),
            "can_find_kernel_file": all(
                (submitted / name).is_file() for name in kernel_files
            ),
            "can_parse_output": False,
        }
        if modified:
            checks["submission_error"] = (
                "Original protected files were modified or removed"
            )
            return checks, {}, DesignSpaceExplicit()
        try:

            def regular_file(name: str) -> Path:
                path = submitted / name
                if (
                    not path.is_file()
                    or path.is_symlink()
                    or not path.resolve().is_relative_to(submitted.resolve())
                ):
                    raise ValueError(f"Missing or unsafe submission file: {name}")
                return path

            templates = {name: regular_file(name).read_text() for name in kernel_files}
            jsonl = regular_file("design_space.jsonl").read_text()
            lines = [line for line in jsonl.splitlines() if line.strip()]
            if not 2 <= len(lines) <= self.max_design_points:
                raise ValueError(
                    f"Expected 2..{self.max_design_points} design-space points, got {len(lines)}"
                )
            space = DesignSpaceExplicit()
            space.parse_from_jsonl("\n".join(lines))
            if any(
                isinstance(value, float) and not math.isfinite(value)
                for point in space.design_space
                for value in point.values()
            ):
                raise ValueError("Design-space numbers must be finite")
            canonical = [
                json.dumps(point, sort_keys=True) for point in space.design_space
            ]
            if len(set(canonical)) != len(canonical):
                raise ValueError("Design-space assignments must be distinct")
            checks["can_parse_output"] = True
            return checks, templates, space
        except (OSError, ValueError, TypeError) as error:
            checks["submission_error"] = str(error)
            return checks, {}, DesignSpaceExplicit()

    def _evaluate_point(
        self,
        original: Path,
        eval_dir: Path,
        kernel_files: list[str],
        tb_file: str,
        top_function: str,
        pools: EvalThreadPools,
        baseline: dict,
        original_interfaces: dict[str, list[str]],
        templates: dict[str, str],
        index: int,
        assignment: dict,
    ) -> dict:
        point_dir = eval_dir / "points" / f"point__{index}"
        point_dir.mkdir(parents=True)
        point: dict[str, Any] = {
            "point_index": index,
            "parameters": assignment,
            "render_success": False,
            "passed": False,
        }
        try:
            rendered = JinjaParamaterizationFlow(
                strict_undefined=True,
                sandboxed=True,
            ).preprocess(
                templates,
                DesignSpaceExplicit([assignment]),
            )[0]
            if any(
                marker in source
                for source in rendered.values()
                for marker in ("{{", "{%", "{#")
            ):
                raise ValueError("Unexpanded Jinja syntax remains in rendered sources")
            point["render_success"] = True
            digest = hashlib.sha256(
                json.dumps(rendered, sort_keys=True).encode()
            ).hexdigest()
            point["source_sha256"] = digest
            design_dir = point_dir / "design"
            shutil.copytree(original, design_dir)
            for name, source in rendered.items():
                (design_dir / name).write_text(source)
            point.update(
                self._evaluate_variant(
                    design_dir,
                    kernel_files,
                    tb_file,
                    top_function,
                    pools,
                    expected_signatures=baseline.get("top_signatures", []),
                )
            )
            point["interface_pragmas_preserved"] = (
                _interface_pragmas(rendered) == original_interfaces
            )
            point["interface_preserved"] &= point["interface_pragmas_preserved"]
            point["passed"] &= point["interface_preserved"]
        except Exception as error:
            point["error"] = f"{type(error).__name__}: {error}"
        (point_dir / "result.json").write_text(json.dumps(point, indent=4))
        return point

    def _evaluate_sample(
        self,
        original: Path,
        agent_dir: Path,
        eval_dir: Path,
        kernel_files: list[str],
        tb_file: str,
        top_function: str,
        pools: EvalThreadPools,
    ) -> dict:
        checks, templates, space = self._read_submission(
            original, agent_dir, kernel_files, tb_file
        )
        result: dict[str, Any] = {**checks, "passed": False, "points": []}
        if not checks["can_parse_output"]:
            return result
        (eval_dir / "design_space.jsonl").write_text(space.render_to_jsonl() + "\n")
        baseline_dir = eval_dir / "baseline" / "design"
        shutil.copytree(original, baseline_dir)
        baseline = self._evaluate_variant(
            baseline_dir, kernel_files, tb_file, top_function, pools
        )
        result["baseline"] = baseline
        (baseline_dir.parent / "result.json").write_text(json.dumps(baseline, indent=4))
        original_interfaces = _interface_pragmas(
            {name: (original / name).read_text() for name in kernel_files}
        )

        # Each point only blocks on the shared csim/synth pools, never on this
        # one, so sizing it to the point count runs every point concurrently
        # without risking a self-submit-and-wait deadlock on pools.pool_csim
        # or pools.pool_synth.
        points_by_index: dict[int, dict] = {}
        with ThreadPoolExecutor(
            max_workers=len(space.design_space), thread_name_prefix="eval-point"
        ) as pool_points:
            futures = {
                pool_points.submit(
                    self._evaluate_point,
                    original,
                    eval_dir,
                    kernel_files,
                    tb_file,
                    top_function,
                    pools,
                    baseline,
                    original_interfaces,
                    templates,
                    index,
                    assignment,
                ): index
                for index, assignment in enumerate(space.design_space)
            }
            for future in as_completed(futures):
                points_by_index[futures[future]] = future.result()

        seen_sources: dict[str, int] = {}
        points = []
        for index in range(len(space.design_space)):
            point = points_by_index[index]
            if point.get("render_success"):
                digest = point["source_sha256"]
                point["duplicate_of"] = seen_sources.get(digest)
                seen_sources.setdefault(digest, index)
            points.append(point)
        result["points"] = points

        result["summary"] = summarize_design_space(result["points"], baseline)
        result["passed"] = (
            all(point["passed"] for point in result["points"])
            and len(seen_sources) >= 2
        )
        return result

    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
        **kwargs,
    ) -> None:
        if not isinstance(model.llm, OpenRouterChat):
            raise NotImplementedError(
                "Pi evaluation currently requires an OpenRouter model"
            )
        if model.llm.key is None:
            raise ValueError(f"API key not found for model {model.name}")
        normalized = normalize_model_name(model.name)
        eval_id = f"{benchmark_case.name}__{normalized}"
        eval_top = (self.output_data_dir / eval_id).resolve()
        if eval_top.exists():
            shutil.rmtree(eval_top)
        eval_top.mkdir(parents=True)
        original = benchmark_case.design_dir.resolve()
        tb_file = benchmark_case.tb_file.relative_to(
            benchmark_case.design_dir
        ).as_posix()
        kernel_files = sorted(
            p.relative_to(original).as_posix()
            for p in original.rglob("*")
            if p.is_file()
            and p.suffix in CPP_EXTENSIONS
            and p.relative_to(original).as_posix() != tb_file
        )
        if not kernel_files:
            raise ValueError(
                "The benchmark must contain complete kernel implementation files"
            )
        prompt = build_prompt_parameterization(
            kernel_files,
            benchmark_case.top_fn,
            self.max_design_points,
            self.hls_fpga_part,
            self.hls_clock_period_ns,
            vitis_available=self.vitis_dir is not None,
        )
        all_data = {}
        for sample_index in range(self.n_samples):
            eval_dir = eval_top / f"sample__{sample_index}"
            eval_dir.mkdir()
            design_dir, agent_dir = eval_dir / "design", eval_dir / "agent_run_dir"
            shutil.copytree(original, design_dir)
            shutil.copytree(original, agent_dir)
            data: dict[str, Any] = {
                "eval_type": "hls_parameterization_agentic_pi",
                "eval_id": eval_id,
                "benchmark_case_name": benchmark_case.name,
                "benchmark_case_tags": benchmark_case.tags_all,
                "model_name": model.name,
                "model_name_normalized": normalized,
                "docker_image_name": self.docker_image_name,
                "n_samples": self.n_samples,
                "sample_index": sample_index,
                "prompt": prompt,
                "passed": False,
                "configuration": {
                    "clang_bin": self.clang_bin,
                    "clang_flags": self.clang_flags,
                    "max_design_points": self.max_design_points,
                    "hls_fpga_part": self.hls_fpga_part,
                    "hls_clock_period_ns": self.hls_clock_period_ns,
                    "compile_timeout": self.compile_timeout,
                    "csim_timeout": self.csim_timeout,
                    "synth_timeout": self.synth_timeout,
                },
            }
            (eval_dir / "raw_agent_prompt.txt").write_text(prompt)
            self.logger.info("[%s] Parameterizing sample %d", eval_id, sample_index)
            start = time.monotonic()
            try:
                agent = pools.pool_agent.submit(
                    run_pi_agent,
                    agent_run_dir=agent_dir,
                    prompt=prompt,
                    model_name=model.llm.model_name,
                    api_key=model.llm.key,
                    docker_image_name=self.docker_image_name,
                    vitis_dir=self.vitis_dir,
                    vivado_dir=self.vivado_dir,
                    vitis_license_server=self.vitis_license_server,
                ).result()
                end = time.monotonic()
                data.update(
                    {
                        "agent_execution_time": {
                            "t0": start,
                            "t1": end,
                            "execution_time": end - start,
                        },
                        "agent_submitted": agent.agent_submitted,
                        "agent_limit_exceeded": agent.agent_limit_exceeded,
                        "agent_exit_code": agent.exit_code,
                        "agent_output": agent.output,
                        "agent_trace": agent.agent_trace,
                    }
                )
                (eval_dir / "agent_output.txt").write_text(agent.output)
                (eval_dir / "trace.json").write_text(
                    json.dumps(agent.agent_trace, indent=4)
                )
                if agent.session_file is not None:
                    shutil.copy(agent.session_file, eval_dir / agent.session_file.name)
                if (
                    agent.session_html_file is not None
                    and agent.session_html_file.exists()
                ):
                    shutil.copy(agent.session_html_file, eval_dir / "trace.html")
                if agent.agent_submitted and not agent.agent_limit_exceeded:
                    data.update(
                        self._evaluate_sample(
                            design_dir,
                            agent_dir,
                            eval_dir,
                            kernel_files,
                            tb_file,
                            benchmark_case.top_fn,
                            pools,
                        )
                    )
            except Exception as error:
                self.logger.exception(
                    "[%s] Parameterization evaluation failed", eval_id
                )
                data["error"] = f"{type(error).__name__}: {error}"
            serialize_eval_data(eval_id, eval_dir, data)
            all_data[sample_index] = data
        (eval_top / "all_eval_data.json").write_text(json.dumps(all_data, indent=4))


class HLSParameterizationIteratativeAgentEvaluatorPi(HLSGenerationAgentEvaluatorPi): ...
