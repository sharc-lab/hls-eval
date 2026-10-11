"""Functional checks for self-checking testbenches and complete reference dumps."""

import hashlib
import json
import re
from dataclasses import asdict
from decimal import Decimal, localcontext
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from hls_eval.data import BenchmarkCase
    from hls_eval.tools import ToolDataOutput, VitisHLSCSimTool

NUMBER = re.compile(
    r"[-+]?(?:nan|inf(?:inity)?|(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?)",
    re.IGNORECASE,
)


def compare_dump(
    actual: str,
    expected: str,
    *,
    kind: str,
    abs_tol: str = "1e-9",
    rel_tol: str = "1e-6",
) -> dict:
    """Compare every token, retaining labels, shape and raw AP bit patterns."""
    got, want = actual.split(), expected.split()
    if not want:
        raise ValueError("Reference output is empty")
    if kind not in {"numeric_dump", "exact_tokens"}:
        raise ValueError(f"Unknown dump comparison: {kind}")
    if len(got) != len(want):
        return {
            "passed": False,
            "reason": "shape mismatch",
            "actual_count": len(got),
            "expected_count": len(want),
        }
    absolute, relative = Decimal(abs_tol), Decimal(rel_tol)
    for index, (a, b) in enumerate(zip(got, want)):
        if kind == "numeric_dump" and NUMBER.fullmatch(b):
            if not NUMBER.fullmatch(a):
                equal = False
            else:
                x, y = Decimal(a), Decimal(b)
                with localcontext() as context:
                    context.prec = max(64, len(a) + len(b) + 32)
                    equal = (
                        x.is_finite()
                        and y.is_finite()
                        and abs(x - y) <= max(absolute, relative * abs(y))
                    )
        else:
            equal = a == b
        if not equal:
            return {
                "passed": False,
                "reason": "output mismatch",
                "first_mismatch": index,
                "actual": a,
                "expected": b,
            }
    return {"passed": True, "reason": "matched", "token_count": len(want)}


def execution_succeeded(output: "ToolDataOutput | None") -> bool:
    return (
        output is not None
        and output.data_execution.return_code == 0
        and not output.data_execution.timeout
    )


def functional_passed(output: "ToolDataOutput | None") -> bool:
    return (
        execution_succeeded(output)
        and output.data_tool is not None
        and output.data_tool.get("functional_check", {}).get("passed") is True
    )


def recorded_functional_result(record: dict) -> bool | None:
    """Historical execution-only results and fixture errors remain unverified."""
    if "functional_check" in record:
        return record["functional_check"]["passed"]
    if record.get("can_parse_output") is False:
        return False
    for stage in ("c_compile_out", "c_run_out"):
        if stage in record:
            execution = record[stage]["data_execution"]
            if execution["return_code"] != 0 or execution.get("timeout", False):
                return False
    return None


def run_checked_csim(
    tool: "VitisHLSCSimTool",
    case: "BenchmarkCase",
    build_dir: Path,
    source_files: list[Path],
    aux_files: list[Path] | None = None,
    build_name: str | None = None,
    **kwargs,
) -> tuple["ToolDataOutput", "ToolDataOutput | None"]:
    """Keep execution evidence intact; check against the trusted original case.

    Dump references run with the same SDK, defines and CSim options as candidates.
    Reference evidence is saved in a separate build before the candidate runs.
    Undeclared cases remain unverified, even when their executable exits zero.
    """
    policy = case.toml_data.get("comparison")
    reference_compile = reference_run = None
    reference_error = None
    reference_sha256 = {}
    if policy and policy["kind"] in {"numeric_dump", "exact_tokens"}:
        try:
            sources, data = case.source_files, case.tb_data_files
            reference_sha256 = {
                p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                for p in [
                    *sources,
                    *data,
                    case.kernel_description_fp,
                    case.design_dir / "hls_eval_config.toml",
                ]
            }
            reference_compile, reference_run = tool.run(
                build_dir / "functional_reference",
                sources,
                aux_files=data,
                build_name=build_name,
                **kwargs,
            )
        except OSError as error:
            reference_error = str(error)
        reference_evidence = {
            "compile": asdict(reference_compile) if reference_compile else None,
            "run": asdict(reference_run) if reference_run else None,
            "error": reference_error,
            "files_sha256": reference_sha256,
            "csim_options": {"sdk": str(tool.vitis_hls_path), **kwargs},
            "policy": policy,
        }
        evidence_path = build_dir / "functional_reference" / "reference_check.json"
        evidence_path.parent.mkdir(parents=True, exist_ok=True)
        evidence_path.write_text(
            json.dumps(reference_evidence, indent=2), encoding="utf-8"
        )
    # Candidate edits to a testbench cannot change the functional oracle.
    sources = [p for p in source_files if not p.stem.endswith("_tb")]
    sources.append(case.tb_file)
    compiled, run = tool.run(
        build_dir, sources, aux_files=aux_files or [], build_name=build_name, **kwargs
    )
    check = {
        "status": "unverified",
        "passed": None,
        "reason": "No comparison policy declared",
    }
    if policy:
        kind = policy["kind"]
        if kind not in {"exit_code", "numeric_dump", "exact_tokens"}:
            raise ValueError(f"Unknown comparison policy: {kind}")
        if kind == "exit_code":
            passed = execution_succeeded(compiled) and execution_succeeded(run)
            check = {
                "status": "passed" if passed else "failed",
                "passed": passed,
                "reason": "Self-checking testbench",
                "kind": kind,
            }
        else:
            check = {"status": "fixture_error", "passed": None, "kind": kind}
            if not (
                execution_succeeded(reference_compile)
                and execution_succeeded(reference_run)
            ):
                check["reason"] = (
                    reference_error or "Reference compilation or execution failed"
                )
            else:
                expected = getattr(reference_run.data_execution, policy["channel"])
                tokens = expected.split()
                if not tokens or len(tokens) != policy["token_count"]:
                    check["reason"] = "Reference output is empty or incomplete"
                elif any(
                    marker not in expected
                    for marker in policy.get("completion_markers", [])
                ):
                    check["reason"] = "Reference completion marker missing"
                elif kind == "numeric_dump" and any(
                    NUMBER.fullmatch(t) and not Decimal(t).is_finite() for t in tokens
                ):
                    check["reason"] = "Reference contains nonfinite values"
                elif not (execution_succeeded(compiled) and execution_succeeded(run)):
                    check.update(
                        status="failed",
                        passed=False,
                        reason="Candidate execution failed",
                    )
                else:
                    actual = getattr(run.data_execution, policy["channel"])
                    check.update(
                        compare_dump(
                            actual,
                            expected,
                            kind=kind,
                            abs_tol=policy.get("abs_tol", "1e-9"),
                            rel_tol=policy.get("rel_tol", "1e-6"),
                        )
                    )
                    check["status"] = "passed" if check["passed"] else "failed"
                check["expected_sha256"] = hashlib.sha256(expected.encode()).hexdigest()
            check["reference_evidence"] = str(evidence_path)
    evidence_output = run if run is not None else compiled
    evidence_output.data_tool = {
        **(evidence_output.data_tool or {}),
        "functional_check": check,
    }
    return compiled, run
