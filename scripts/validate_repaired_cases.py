"""Compile the 62 reviewed fixtures on a host with Vitis AP headers.

This is native C++ validation, not Vitis CSim or synthesis. Outputs and compiler
logs stay in --output; the JSON summary records source hashes and token counts.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hls_eval.comparison import compare_dump
from hls_eval.data import BenchmarkCase


def validate(directory, output, compiler, sdk):
    case = BenchmarkCase(directory)
    name = directory.relative_to(ROOT / "hls_eval_data").as_posix()
    work = output / name
    work.mkdir(parents=True, exist_ok=True)
    for data in case.tb_data_files:
        # These reviewed fixtures use text inputs. Match Git's LF contents.
        (work / data.name).write_bytes(data.read_bytes().replace(b"\r\n", b"\n"))
    executable = work / ("test.exe" if os.name == "nt" else "test")
    cmd = [
        compiler,
        "-std=c++14",
        "-O1",
        "-fno-fast-math",
        "-Wno-unknown-pragmas",
        "-I",
        str(directory),
        "-I",
        str(sdk / "include"),
        *map(str, case.cpp_files),
        "-o",
        str(executable),
    ]
    if os.name == "nt":
        # MachSuite readfile uses fstat byte lengths, so POSIX open/read semantics
        # are needed when compiling its Linux fixture with a Windows CRT.
        binary_io = work / "native_binary_io.cpp"
        binary_io.write_text(
            "#include <stdlib.h>\n#include <fcntl.h>\n"
            "struct BinaryMode { BinaryMode() { _set_fmode(_O_BINARY); } };\n"
            "static BinaryMode mode;\n",
            encoding="utf-8",
        )
        cmd.insert(-2, str(binary_io))
        cmd.append("-Wl,--stack,33554432")
    compiled = subprocess.run(cmd, capture_output=True, timeout=180, check=False)
    (work / "compile.log").write_bytes(compiled.stdout + compiled.stderr)
    result = {
        "case": name,
        "command": cmd,
        "compile_rc": compiled.returncode,
        "files_sha256": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in [*case.source_files, *case.tb_data_files]
        },
        "passed": False,
    }
    if compiled.returncode != 0:
        return result
    try:
        run = subprocess.run(
            [str(executable)], cwd=work, capture_output=True, timeout=180, check=False
        )
    except subprocess.TimeoutExpired:
        result["timeout"] = True
        return result
    (work / "stdout.txt").write_bytes(run.stdout)
    (work / "stderr.txt").write_bytes(run.stderr)
    result["run_rc"] = run.returncode
    policy = case.toml_data["comparison"]
    result["passed"] = run.returncode == 0
    if policy["kind"] != "exit_code" and result["passed"]:
        text = getattr(run, policy["channel"]).decode("utf-8", errors="replace")
        result["token_count"] = len(text.split())
        result["output_sha256"] = hashlib.sha256(text.encode()).hexdigest()
        result["comparison"] = compare_dump(text, text, kind=policy["kind"])
        result["passed"] &= result["comparison"]["passed"]
        result["passed"] &= all(m in text for m in policy.get("completion_markers", []))
        if "token_count" in policy:
            result["passed"] &= result["token_count"] == policy["token_count"]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vitis-home", type=Path, default=os.environ.get("VITIS_HOME"))
    parser.add_argument("--compiler", default=shutil.which("g++"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=3)
    args = parser.parse_args()
    if args.vitis_home is None or args.compiler is None:
        parser.error("Supply --vitis-home (or VITIS_HOME) and a C++ compiler")
    cases = [
        p.parent
        for p in (ROOT / "hls_eval_data").rglob("hls_eval_config.toml")
        if "[comparison]" in p.read_text()
    ]
    results = []
    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        futures = [
            pool.submit(
                validate,
                p,
                args.output.resolve(),
                args.compiler,
                args.vitis_home.resolve(),
            )
            for p in sorted(cases)
        ]
        for future in as_completed(futures):
            result = future.result()
            results.append(result)
            print(
                json.dumps(
                    {
                        k: v
                        for k, v in result.items()
                        if k not in {"command", "files_sha256"}
                    }
                ),
                flush=True,
            )
    summary = {
        "validation": "native_cpp",
        "sdk": str(args.vitis_home.resolve()),
        "results": sorted(results, key=lambda r: r["case"]),
        "passed": sum(r["passed"] for r in results),
        "total": len(results),
    }
    (args.output / "results.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    return 0 if summary["passed"] == summary["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
