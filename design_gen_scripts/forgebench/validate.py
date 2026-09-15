"""Compile and run isolated ForgeBench testbenches with installed Vitis headers.

Validates C simulation, not synthesis or RTL cosimulation. Array-bounds checks stop on invalid kernel array accesses. Logs and actual outputs stay in --work-dir.
"""

from __future__ import annotations
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
import re
from pathlib import Path
import shutil
import signal
import subprocess
import time
from generate import ROOT


def validate(design, args):
    work = args.work_dir / design.name
    work.mkdir(parents=True, exist_ok=True)
    manifest = json.loads((design / "testbench.json").read_text())
    for filename in set(manifest["inputs"].values()) | set(
        manifest["outputs"].values()
    ):
        shutil.copyfile(design / filename, work / filename)
    command = [
        args.cxx,
        "-std=c++14",
        "-O1",
        "-Wno-unknown-pragmas",
        "-I",
        str(args.hls_include),
        str(design / "top.cpp"),
        str(design / "tb_top.cpp"),
        "-lgmp",
        "-o",
        str(work / "testbench"),
    ]
    library = args.hls_include.parent / "lnx64" / "lib" / "csim"
    if library.is_dir():
        fpo = args.hls_include.parent / "lnx64" / "tools" / "fpo_v7_1"
        command += [
            "-L",
            str(library),
            "-Wl,--disable-new-dtags",
            "-Wl,-rpath," + str(library),
            "-lhlsmc++-GCC46",
            "-lhlsm-GCC46",
            "-L",
            str(fpo),
            "-Wl,-rpath," + str(fpo),
            "-lIp_floating_point_v7_1_bitacc_cmodel",
            "-lmpfr",
        ]
    if not args.no_sanitize:
        command[1:1] = [
            "-fsanitize=bounds",
            "-fno-sanitize-recover=all",
            "-fno-omit-frame-pointer",
        ]
    result = {
        "compile_command": command,
        "functional_coverage_complete": manifest["functional_coverage_complete"],
        "golden_arithmetic": manifest["golden_arithmetic"],
        "kernel_arithmetic": manifest["kernel_arithmetic"],
        "atol": manifest["atol"],
        "rtol": manifest["rtol"],
    }
    for phase, cmd in [("compile", command), ("run", [str(work / "testbench")])]:
        start = time.monotonic()
        try:
            with (work / (phase + ".log")).open("w") as log:
                completed = subprocess.run(
                    cmd,
                    cwd=work,
                    stdout=log,
                    stderr=subprocess.STDOUT,
                    timeout=args.compile_timeout
                    if phase == "compile"
                    else args.timeout,
                )
            result[phase + "_seconds"] = round(time.monotonic() - start, 2)
            result[phase + "_returncode"] = completed.returncode
            if phase == "run":
                log_text = (work / "run.log").read_text(errors="replace")
                result["outputs"] = {
                    match[2]: {
                        "status": match[1].lower(),
                        "mismatches": int(match[3]),
                        "count": int(match[4]),
                        "max_abs_error": float(match[5]),
                    }
                    for match in re.finditer(
                        r"(PASS|FAIL): (\w+) \((\d+)/(\d+) mismatches, max_abs_error=([^,]+),",
                        log_text,
                    )
                }
            if completed.returncode:
                text = (work / (phase + ".log")).read_text(errors="replace")
                result["status"] = (
                    "compile_error"
                    if phase == "compile"
                    else "arithmetic_error"
                    if completed.returncode == -signal.SIGFPE
                    else "memory_error"
                    if "Sanitizer" in text or "runtime error:" in text
                    else "mismatch"
                    if "FAIL:" in text
                    else "incomplete_coverage"
                    if "INCOMPLETE COVERAGE:" in text
                    else "run_error"
                )
                if completed.returncode < 0:
                    result["signal"] = signal.Signals(-completed.returncode).name
                return result
        except subprocess.TimeoutExpired:
            result["status"] = phase + "_timeout"
            return result
    if set(result.get("outputs", {})) != set(manifest["outputs"]):
        result["status"] = "incomplete_coverage"
        return result
    result["status"] = "pass"
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--hls-include", type=Path, required=True)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--design", action="append")
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--timeout", type=int, default=300)
    parser.add_argument("--compile-timeout", type=int, default=180)
    parser.add_argument("--cxx", default="g++")
    parser.add_argument("--no-sanitize", action="store_true")
    args = parser.parse_args()
    args.root, args.work_dir, args.hls_include = (
        args.root.resolve(),
        args.work_dir.resolve(),
        args.hls_include.resolve(),
    )
    if not (args.hls_include / "ap_fixed.h").is_file():
        parser.error("--hls-include must contain ap_fixed.h")
    if args.work_dir == args.root or args.root in args.work_dir.parents:
        parser.error("Use a work directory outside the source dataset")
    designs = sorted(p.parent for p in args.root.glob("*/top.cpp"))
    if not designs:
        parser.error("No designs found")
    missing = [d.name for d in designs if not (d / "testbench.json").is_file()]
    if missing:
        parser.error(f"Designs missing correctness manifests: {missing}")
    if args.design:
        unknown = set(args.design) - {p.name for p in designs}
        if unknown:
            parser.error(f"Unknown designs: {sorted(unknown)}")
        designs = [p for p in designs if p.name in args.design]
    args.work_dir.mkdir(parents=True, exist_ok=True)
    report = {}
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        pending = {
            pool.submit(validate, design, args): design.name for design in designs
        }
        for future in as_completed(pending):
            name = pending[future]
            try:
                report[name] = future.result()
            except Exception as exc:
                report[name] = {"status": "validation_error", "error": str(exc)}
            print(name + ": " + report[name]["status"], flush=True)
            (args.work_dir / "report.json").write_text(
                json.dumps(dict(sorted(report.items())), indent=2) + "\n"
            )
    raise SystemExit(0 if all(r["status"] == "pass" for r in report.values()) else 1)


if __name__ == "__main__":
    main()
