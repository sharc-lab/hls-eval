"""Regenerate temporary float kernels to cross-check the float64 goldens.

The imported dataset remains fixed-point. This control uses identical effective
configs, inputs, goldens, and the same absolute 1e-3 comparator.
"""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
from generate import HERE, ROOT, emit_kernel, render_testbench


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--work-dir", type=Path, required=True)
    parser.add_argument("--hls-include", type=Path, required=True)
    parser.add_argument("--jobs", type=int, default=8)
    parser.add_argument(
        "--report", type=Path, default=HERE / "float_control_results.json"
    )
    args = parser.parse_args()
    root, work = args.root.resolve(), args.work_dir.resolve()
    if work == root or root in work.parents:
        parser.error("Use a control directory outside the fixed-point dataset")
    sources = work / "sources"
    for path in sorted(root.glob("*/testbench.json")):
        manifest = json.loads(path.read_text())
        config = json.loads((path.parent / "config.json").read_text())
        config["data_type"] = "float"
        design = sources / path.parent.name
        design.mkdir(parents=True, exist_ok=True)
        emit_kernel(manifest["domain"], config, design)
        (design / "tb_top.cpp").write_text(
            render_testbench(
                manifest["arrays"],
                manifest["inputs"],
                manifest["outputs"],
                data_type="float",
            )
        )
        shutil.copyfile(HERE / "tb_support.h", design / "tb_support.h")
        for f in {*manifest["inputs"].values(), *manifest["outputs"].values()}:
            shutil.copyfile(path.parent / f, design / f)
        manifest = {
            k: manifest[k]
            for k in [
                "domain",
                "arrays",
                "inputs",
                "outputs",
                "atol",
                "rtol",
                "functional_coverage_complete",
                "golden_arithmetic",
                "upstream",
            ]
        }
        manifest["kernel_arithmetic"] = "float32"
        manifest["purpose"] = (
            "Temporary float control; production dataset remains fixed-point"
        )
        (design / "testbench.json").write_text(json.dumps(manifest, indent=2) + "\n")
    completed = subprocess.run(
        [
            sys.executable,
            str(HERE / "validate.py"),
            "--root",
            str(sources),
            "--work-dir",
            str(work / "runs"),
            "--hls-include",
            str(args.hls_include),
            "--jobs",
            str(args.jobs),
            "--timeout",
            "600",
        ],
        check=False,
    )
    results = json.loads((work / "runs" / "report.json").read_text())
    for path in sorted(root.glob("*/testbench.json")):
        manifest = json.loads(path.read_text())
        for filename in {*manifest["inputs"].values(), *manifest["outputs"].values()}:
            original = (path.parent / filename).read_bytes()
            control = (sources / path.parent.name / filename).read_bytes()
            if hashlib.sha256(original).digest() != hashlib.sha256(control).digest():
                raise ValueError(
                    "Float control fixture differs from fixed-point fixture"
                )
    args.report.write_text(
        json.dumps(
            {
                "upstream": json.loads((root / "suite.json").read_text())["upstream"],
                "fixture_hashes_identical": True,
                "results": {
                    name: {k: v for k, v in entry.items() if k != "compile_command"}
                    for name, entry in results.items()
                },
            },
            indent=2,
        )
        + "\n"
    )
    raise SystemExit(completed.returncode)


if __name__ == "__main__":
    main()
