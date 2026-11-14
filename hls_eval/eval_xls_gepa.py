"""XLS DSLX source optimization with a protected test bench and GEPA.

This evaluator is separate from the C/C++ Vitis evaluators in ``eval.py``.
It requires built XLS command-line tools and, for search, the optional GEPA
package and a caller-provided reflection model.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import time
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable


TOOL_PATHS = {
    "interpreter": "xls/dslx/interpreter_main",
    "convert": "xls/dslx/ir_convert/ir_converter_main",
    "opt": "xls/tools/opt_main",
    "codegen": "xls/tools/codegen_main",
    "delay": "xls/tools/delay_info_main",
    "formal": "xls/dev_tools/check_ir_equivalence_main",
}


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _split_tests(source: str) -> tuple[str, str, int]:
    """Remove DSLX test functions while preserving the rest of the source."""
    masked = re.sub(
        r'//[^\n]*|/\*.*?\*/|"(?:\\.|[^"\\])*"',
        lambda match: " " * len(match.group()),
        source,
        flags=re.S,
    )
    spans: list[tuple[int, int]] = []
    for match in re.finditer(r"#\[test\]\s*fn\s+\w+\s*\(", masked):
        start = masked.find("{", match.end())
        if start < 0:
            raise ValueError("Malformed DSLX test function")
        depth, end = 1, start + 1
        while depth and end < len(masked):
            if masked[end] == "{":
                depth += 1
            elif masked[end] == "}":
                depth -= 1
            end += 1
        if depth:
            raise ValueError("Unclosed DSLX test function")
        spans.append((match.start(), end))
    implementation = source
    for start, end in reversed(spans):
        implementation = implementation[:start] + implementation[end:]
    tests = "\n\n".join(source[start:end] for start, end in spans)
    return implementation, tests, len(spans)


def _ir_signature(ir: str) -> str:
    match = re.search(r"top fn \w+\((.*?)\)\s*->\s*([^\{]+)\{", ir, re.S)
    if not match:
        raise ValueError("Converted IR has no top function")
    signature = f"({match.group(1)})->{match.group(2)}"
    return re.sub(r"\s+|\bid=\d+\b", "", signature)


def _dslx_signature(source: str, top: str) -> str:
    uncommented = re.sub(r"//[^\n]*|/\*.*?\*/", "", source, flags=re.S)
    match = re.search(r"\b(?:pub\s+)?fn\s+" + re.escape(top) +
                      r"\s*\((.*?)\)\s*->\s*([^\{]+)\{", uncommented, re.S)
    if not match:
        raise ValueError(f"Missing DSLX top function: {top}")
    return re.sub(r"\s+", "", f"({match.group(1)})->{match.group(2)}")


def _critical_path(text: str) -> int:
    if "# Critical path:" not in text:
        raise ValueError("XLS delay report has no critical path section")
    section = text.split("# Critical path:")[-1].split("\n\n")[0]
    delays = [int(value) for value in re.findall(r"^\s*(\d+)ps\s+\(", section, re.M)]
    if not delays:
        raise ValueError("XLS delay report has no parseable path values")
    return max(delays)


@dataclass(frozen=True)
class XLSGepaConfig:
    top: str
    pipeline_stages: int = 1
    delay_model: str = "unit"
    secondary_delay_model: str | None = "asap7"
    opt_level: int = 3
    command_timeout_seconds: int = 180
    formal_timeout_seconds: int = 60
    max_metric_calls: int = 12
    max_model_calls: int = 2
    search_timeout_seconds: int = 1800
    seed: int = 20260930

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z_0-9]*", self.top):
            raise ValueError("top must be a DSLX identifier")
        if self.pipeline_stages < 1 or self.opt_level < 0:
            raise ValueError("pipeline_stages must be positive and opt_level nonnegative")
        if min(self.command_timeout_seconds, self.formal_timeout_seconds,
               self.max_metric_calls, self.max_model_calls,
               self.search_timeout_seconds) < 1:
            raise ValueError("timeouts and budgets must be positive")


class XLSGepaEvaluator:
    """Evaluate DSLX variants against the original design's tests.

    A candidate passes the current correctness gate when the protected test
    bench passes and XLS codegen succeeds. Formal proof is extra evidence;
    a definite counterexample rejects the candidate, while timeout is logged
    as inconclusive. This is not an independent functional specification.
    """

    def __init__(self, source_file: Path, xls_root: Path, work_dir: Path,
                 config: XLSGepaConfig):
        self.source_file = Path(source_file).resolve()
        self.xls_root = Path(xls_root).resolve()
        self.work_dir = Path(work_dir).resolve()
        self.config = config
        if not self.source_file.is_file() or self.source_file.suffix != ".x":
            raise ValueError("source_file must be an existing DSLX .x file")
        self.original = self.source_file.read_text(encoding="utf-8")
        self.implementation, self.tests, self.test_count = _split_tests(self.original)
        if self.test_count == 0:
            raise ValueError("The original DSLX design must contain at least one #[test] function")
        self.top_signature = _dslx_signature(self.implementation, config.top)
        self.source_hash = hashlib.sha256(self.source_file.read_bytes()).hexdigest()
        self.work_dir.mkdir(parents=True, exist_ok=True)
        manifest = self.work_dir / "gepa_config.json"
        prepared = {"source_file": str(self.source_file),
                    "source_sha256": self.source_hash,
                    "xls_root": str(self.xls_root), "test_count": self.test_count,
                    "tool_sha256": self._tool_fingerprints(),
                    "evaluator_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                    "correctness_gate": "protected_original_dslx_tests_and_codegen",
                    "formal_policy": "counterexample_rejects; timeout_inconclusive",
                    "config": asdict(config)}
        if manifest.exists() and json.loads(manifest.read_text()) != prepared:
            raise ValueError("Work directory belongs to a different source or configuration")
        manifest.write_text(json.dumps(prepared, indent=2) + "\n")

    def _tool(self, name: str) -> Path:
        path = self.xls_root / "bazel-bin" / TOOL_PATHS[name]
        if not path.is_file():
            raise FileNotFoundError(f"Missing built XLS tool: {path}")
        return path

    def _tool_fingerprints(self) -> dict[str, str]:
        required = ("interpreter", "convert", "opt", "codegen", "delay")
        hashes = {name: hashlib.sha256(self._tool(name).read_bytes()).hexdigest()
                  for name in required}
        formal = self.xls_root / "bazel-bin" / TOOL_PATHS["formal"]
        if formal.is_file():
            hashes["formal"] = hashlib.sha256(formal.read_bytes()).hexdigest()
        return hashes

    def _run(self, command: list[str | Path], directory: Path, label: str,
             timeout: int | None = None, required: bool = True) -> tuple[str, str, dict]:
        argv = [str(part) for part in command]
        started = time.monotonic()
        try:
            process = subprocess.run(argv, cwd=self.xls_root, capture_output=True,
                                     timeout=timeout or self.config.command_timeout_seconds,
                                     check=False)
            stdout = process.stdout.decode(errors="replace")
            stderr = process.stderr.decode(errors="replace")
            code, timed_out = process.returncode, False
        except subprocess.TimeoutExpired as error:
            stdout = (error.stdout or b"").decode(errors="replace")
            stderr = (error.stderr or b"").decode(errors="replace")
            code, timed_out = None, True
        record = {"argv": argv, "returncode": code, "timeout": timed_out,
                  "elapsed_seconds": time.monotonic() - started}
        (directory / f"{label}.stdout").write_text(stdout)
        (directory / f"{label}.stderr").write_text(stderr)
        (directory / f"{label}.command.json").write_text(json.dumps(record, indent=2) + "\n")
        if required and (timed_out or code != 0):
            raise RuntimeError(f"{label}: " + ("timeout" if timed_out else stderr[-3000:]))
        return stdout, stderr, record

    def _compile(self, source: Path, directory: Path) -> tuple[Path, Path, str]:
        raw, _, _ = self._run(
            [self._tool("convert"), f"--top={self.config.top}",
             f"--dslx_stdlib_path={self.xls_root / 'xls/dslx/stdlib'}", source],
            directory, "convert")
        raw_path = directory / "raw.ir"
        raw_path.write_text(raw)
        signature = _ir_signature(raw)
        optimized, _, _ = self._run(
            [self._tool("opt"), f"--opt_level={self.config.opt_level}",
             f"--delay_model={self.config.delay_model}", raw_path],
            directory, "opt")
        opt_path = directory / "optimized.ir"
        opt_path.write_text(optimized)
        return raw_path, opt_path, signature

    def evaluate(self, source: str | None = None) -> dict[str, Any]:
        is_baseline = source is None
        candidate = self.original if is_baseline else source
        assert candidate is not None
        split_error = None
        try:
            implementation, _, _ = _split_tests(candidate)
        except ValueError as error:
            implementation, split_error = candidate, str(error)
        source_hash = _sha256(implementation)
        directory = self.work_dir / ("baseline" if is_baseline else f"candidates/{source_hash}")
        directory.mkdir(parents=True, exist_ok=True)
        result_file = directory / "result.json"
        if result_file.exists():
            cached = json.loads(result_file.read_text())
            if is_baseline and cached["correctness_status"] != "passed_testbench":
                raise RuntimeError("Cached original design failed its test bench or XLS flow")
            return cached
        if not is_baseline:
            self.evaluate()
        result: dict[str, Any] = {
            "source_sha256": source_hash, "original_source_sha256": self.source_hash,
            "correctness_status": "not_checked", "testbench_passed": False,
            "formal_status": "not_run", "metrics": {}, "score": 0.0,
            "is_baseline": is_baseline,
        }
        started = time.monotonic()
        (directory / "candidate.x").write_text(implementation)
        protected = directory / "protected_tests.x"
        protected.write_text(implementation + "\n\n" + self.tests + "\n")
        try:
            if split_error:
                raise RuntimeError(split_error)
            # Candidate-supplied tests and imports are never trusted as the oracle.
            if not is_baseline and re.search(r"#\[|\b(import|proc)\b", implementation):
                raise RuntimeError("Candidate implementation contains attributes, imports, or procs")
            if _dslx_signature(implementation, self.config.top) != self.top_signature:
                raise RuntimeError("Candidate changed the DSLX top signature")
            if is_baseline:
                self._run([self._tool("interpreter"),
                           f"--dslx_stdlib_path={self.xls_root / 'xls/dslx/stdlib'}",
                           self.source_file], directory, "original_tests")
            self._run([self._tool("interpreter"),
                       f"--dslx_stdlib_path={self.xls_root / 'xls/dslx/stdlib'}",
                       protected], directory, "protected_tests")
            result["testbench_passed"] = True
            raw, optimized, signature = self._compile(directory / "candidate.x", directory)
            result["ir_signature"] = signature
            if not is_baseline:
                baseline = json.loads((self.work_dir / "baseline/result.json").read_text())
                if signature != baseline["ir_signature"]:
                    raise RuntimeError("Candidate changed the XLS top interface")
            self._run(
                [self._tool("codegen"), "--generator=pipeline",
                 f"--pipeline_stages={self.config.pipeline_stages}",
                 f"--delay_model={self.config.delay_model}",
                 "--flop_inputs=true", "--flop_outputs=true",
                 "--use_system_verilog=true", "--module_name=xls_gepa_candidate",
                 f"--output_verilog_path={directory / 'design.sv'}",
                 f"--output_schedule_path={directory / 'schedule.textproto'}",
                 optimized], directory, "codegen")
            if not (directory / "design.sv").is_file():
                raise RuntimeError("XLS codegen did not produce design.sv")
            delay, _, _ = self._run(
                [self._tool("delay"), f"--delay_model={self.config.delay_model}", optimized],
                directory, "delay")
            critical = _critical_path(delay)
            operations = Counter(re.findall(r"^\s*(?:ret\s+)?\S+:.*?=\s*(\w+)\(",
                                            optimized.read_text(), re.M))
            result["metrics"] = {"critical_path_unit_delay": critical,
                                 "optimized_ir_node_count": sum(operations.values()),
                                 "optimized_ir_operation_counts": dict(sorted(operations.items()))}
            if self.config.secondary_delay_model:
                extra, _, status = self._run(
                    [self._tool("delay"),
                     f"--delay_model={self.config.secondary_delay_model}", optimized],
                    directory, "secondary_delay", required=False)
                if not status["timeout"] and status["returncode"] == 0:
                    try:
                        result["metrics"]["secondary_critical_path_estimate_ps"] = _critical_path(extra)
                    except ValueError:
                        result["secondary_estimate_status"] = "unparseable"
                else:
                    result["secondary_estimate_status"] = "unavailable"
            if not is_baseline:
                formal_tool = self.xls_root / "bazel-bin" / TOOL_PATHS["formal"]
                if formal_tool.is_file():
                    stdout, stderr, formal = self._run(
                        [formal_tool, self.work_dir / "baseline/raw.ir", raw],
                        directory, "formal", timeout=self.config.formal_timeout_seconds,
                        required=False)
                    combined = (stdout + stderr).lower()
                    if formal["timeout"]:
                        result["formal_status"] = "inconclusive_timeout"
                    elif "verified not equivalent" in combined or "counterexample" in combined:
                        result["formal_status"] = "proven_not_equivalent"
                        raise RuntimeError("Formal checker found a counterexample")
                    elif formal["returncode"] == 0 and "verified equivalent" in combined:
                        result["formal_status"] = "proven_equivalent"
                    else:
                        result["formal_status"] = "inconclusive_error"
                else:
                    result["formal_status"] = "unavailable"
            result["correctness_status"] = "passed_testbench"
            result["score"] = 1.0 / (1.0 + critical)
            result["feedback"] = (
                f"Passed {self.test_count} protected DSLX tests and fixed XLS codegen. "
                f"Formal: {result['formal_status']}. Unit-model path: {critical}.")
        except (RuntimeError, ValueError, FileNotFoundError) as error:
            result["correctness_status"] = "rejected"
            result["feedback"] = str(error)
        result["elapsed_seconds"] = time.monotonic() - started
        result_file.write_text(json.dumps(result, indent=2) + "\n")
        if is_baseline and result["correctness_status"] != "passed_testbench":
            raise RuntimeError("Original design failed its test bench or XLS flow: " + result["feedback"])
        return result

    def run_gepa(self, reflection_lm: Callable, prompt: str | None = None) -> dict[str, Any]:
        """Run a bounded GEPA search; the caller supplies the model callback."""
        try:
            import gepa
            from gepa.core.adapter import EvaluationBatch
            from gepa.utils.stop_condition import TimeoutStopCondition
        except ImportError as error:
            raise RuntimeError("Install GEPA before running the search") from error

        baseline = self.evaluate()
        evaluator = self

        class Adapter:
            propose_new_texts = None

            def evaluate(self, batch, candidate, capture_traces=False):
                record = evaluator.evaluate(candidate["dslx"])
                outputs = [record for _ in batch]
                return EvaluationBatch(
                    outputs=outputs, scores=[record["score"] for _ in batch],
                    trajectories=outputs if capture_traces else None)

            def make_reflective_dataset(self, candidate, eval_batch, components_to_update):
                return {"dslx": [{"Inputs": "Protected original DSLX tests and fixed XLS settings",
                                  "Generated Outputs": record["metrics"],
                                  "Feedback": record["feedback"]}
                                 for record in eval_batch.outputs]}

        run_dir = self.work_dir / "runs" / time.strftime("%Y%m%d-%H%M%S", time.gmtime())
        run_dir.mkdir(parents=True, exist_ok=False)
        (run_dir / "run_config.json").write_text(json.dumps({
            "source_sha256": self.source_hash,
            "config": asdict(self.config),
            "reflection_model": getattr(reflection_lm, "model", type(reflection_lm).__name__),
        }, indent=2) + "\n")
        template = prompt or (
            "Rewrite only the DSLX implementation. Preserve the top signature, "
            "test-visible behavior, fixed-width arithmetic, and all original tests. "
            "Return the complete DSLX implementation in one fenced code block. "
            "If unsure, return it unchanged.\n\nCandidate:\n```dslx\n<curr_param>\n```\n\n"
            "XLS feedback:\n<side_info>"
        )
        calls = 0
        model_errors: list[dict[str, str]] = []

        def budgeted_reflection(model_prompt):
            nonlocal calls
            if calls >= self.config.max_model_calls:
                raise RuntimeError("GEPA model-call budget exhausted")
            calls += 1
            try:
                return reflection_lm(model_prompt)
            except Exception as error:
                model_errors.append({"error_type": type(error).__name__,
                                     "message": str(error)})
                raise

        try:
            result = gepa.optimize(
                seed_candidate={"dslx": self.implementation},
                trainset=[{"design": self.source_hash}],
                valset=[{"design": self.source_hash}],
                adapter=Adapter(), reflection_lm=budgeted_reflection,
                reflection_prompt_template=template, reflection_minibatch_size=1,
                max_metric_calls=self.config.max_metric_calls,
                stop_callbacks=[TimeoutStopCondition(self.config.search_timeout_seconds),
                                lambda state: calls >= self.config.max_model_calls],
                skip_perfect_score=False, use_merge=False, seed=self.config.seed,
                run_dir=str(run_dir), cache_evaluation=False,
                display_progress_bar=False, raise_on_exception=True,
            )
        except Exception as error:
            (run_dir / "failure.json").write_text(json.dumps({
                "model_calls": calls, "error_type": type(error).__name__,
                "message": str(error), "model_errors": model_errors,
            }, indent=2) + "\n")
            raise
        (run_dir / "gepa-result.json").write_text(json.dumps(result.to_dict(), indent=2) + "\n")
        best_source = result.best_candidate["dslx"]
        (run_dir / "best.x").write_text(best_source)
        best = self.evaluate(best_source)
        summary = {"baseline": baseline, "best": best, "model_calls": calls,
                   "model_errors": model_errors,
                   "improvement_achieved": best["score"] > baseline["score"],
                   "run_dir": str(run_dir)}
        (run_dir / "summary.json").write_text(json.dumps(summary, indent=2) + "\n")
        return summary
