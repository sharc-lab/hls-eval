"""Write a reviewable report from native fixed-point validation results."""

from __future__ import annotations
import argparse
from collections import Counter
import json
from pathlib import Path
from generate import HERE, ROOT


def summarize(root, work, output):
    suite = json.loads((root / "suite.json").read_text())
    report = json.loads((work / "report.json").read_text())
    if set(report) != set(suite["designs"]):
        raise ValueError("Validation report does not cover every design in suite.json")
    for entry in report.values():
        if entry.get("run_returncode") == -8:
            entry["status"] = "arithmetic_error"
            entry["signal"] = "SIGFPE"
    counts = Counter(r["status"] for r in report.values())
    results = {}
    for name, entry in report.items():
        entry = {k: v for k, v in entry.items() if k != "compile_command"}
        if entry["status"] not in {"pass", "mismatch"}:
            phase = "compile" if entry["status"].startswith("compile") else "run"
            log = (work / name / (phase + ".log")).read_text(errors="replace")
            if entry.get("signal"):
                log = "Process terminated by " + entry["signal"] + "\n" + log
            debug = work / name / "debug.log"
            if debug.is_file():
                log += "\n" + debug.read_text(errors="replace")
            entry["diagnostic"] = log[-6000:]
        results[name] = entry
    output.mkdir(parents=True, exist_ok=True)
    (output / "deviations.json").write_text(json.dumps(results, indent=2) + "\n")
    lines = [
        "# ForgeBench base-config validation",
        "",
        f"Upstream: {suite['upstream']['branch']} at {suite['upstream']['commit']}.",
        "",
        "All kernels use ap_fixed<16,5>. Testbenches compare every declared output element",
        "against independent float64 goldens with abs(actual - golden) <= 1e-3 and no relative allowance.",
        "",
        f"Designs: **{len(report)}**. "
        + "; ".join(f"**{n} {s}**" for s, n in sorted(counts.items()))
        + ".",
        "",
        "Native C simulation uses installed Vitis fixed-point/math headers and libraries,",
        "with GCC array-bounds instrumentation. These results do not include synthesis or RTL cosimulation.",
        "",
        "| Design | Result | Mismatches / compared | Maximum absolute error |",
        "|---|---|---:|---:|",
    ]
    for name, entry in sorted(results.items()):
        outputs = entry.get("outputs", {})
        mismatches = sum(o["mismatches"] for o in outputs.values())
        count = sum(o["count"] for o in outputs.values())
        error = max((o["max_abs_error"] for o in outputs.values()), default=None)
        lines.append(
            f"| {name} | {entry['status']} | {mismatches} / {count} | "
            + (f"{error:.8g}" if error is not None else "not reached")
            + " |"
        )
    control_path = output / "float_control_results.json"
    if control_path.is_file():
        control = json.loads(control_path.read_text())
        if control["upstream"] != suite["upstream"] or set(control["results"]) != set(
            report
        ):
            raise ValueError("Float-control provenance or coverage differs from suite")
        passed = sum(r["status"] == "pass" for r in control["results"].values())
        lines += [
            "",
            "## Float control",
            "",
            f"**{passed}/{len(report)} temporary float kernels pass** against the same float64 goldens",
            "and the same absolute 1e-3 threshold. The configs use the same dimensions and",
            "operations as the fixed-point dataset. Input/golden file hashes were checked",
            "for equality. The saved dataset remains fixed-point.",
            "",
            "See float_control_results.json for per-output errors.",
            "",
        ]
    lines += [
        "",
        "## Config repairs",
        "",
        "Untouched originals are included as upstream_config.json in every design.",
        "The effective config.json contains the fixed-point datatype and these documented data-path repairs:",
        "",
    ]
    for name in suite["designs"]:
        manifest = json.loads((root / name / "testbench.json").read_text())
        for change in manifest["config_adjustments"]:
            lines.append(f"- {name}: {change}")
    lines += ["", "## Exclusions", ""]
    for name, reason in suite["excluded_configs"].items():
        lines.append(f"- {name}: {reason}")
    lines += ["", "## Execution diagnostics", ""]
    diagnostics = [(n, r) for n, r in results.items() if "diagnostic" in r]
    if not diagnostics:
        lines.append(
            "No compile or execution errors. Numerical mismatches are reported above."
        )
    for name, result in diagnostics:
        lines += [f"### {name}", "", "~~~text", result["diagnostic"].strip(), "~~~", ""]
    lines += [
        "",
        "## Limits",
        "",
        "Each design has one deterministic input case. Inputs contain signed values and convolution",
        "weights use two selected input channels per output with varied spatial taps.",
        "This exercises the configured full-size output; it does not exhaust the input space.",
        "Numerical mismatches can reflect quantization, overflow, or remaining kernel defects.",
        "They are not automatically classified as harmless fixed-point error.",
        "",
        f"Full commands, logs, executables, and actual output dumps: {work}.",
        "",
    ]
    (output / "validation_report.md").write_text("\n".join(lines))
    print(dict(counts))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=HERE)
    args = parser.parse_args()
    summarize(args.root, args.work_dir, args.output)


if __name__ == "__main__":
    main()
