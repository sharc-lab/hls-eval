"""Audit suite coverage, provenance, and deterministic floating-point fixtures."""

from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from generate import (
    ROOT,
    UPSTREAM,
    PROVENANCE,
    catalog,
    effective_config,
    golden_outputs,
    interface,
    make_inputs,
)


def audit_design(design):
    m = json.loads((design / "testbench.json").read_text())
    if (m["atol"], m["rtol"], m["golden_arithmetic"], m["kernel_arithmetic"]) != (
        1e-3,
        0,
        "float64",
        "ap_fixed<16,5>",
    ):
        raise ValueError(
            "Expected float64 goldens, fixed-point kernel, absolute tolerance 1e-3"
        )
    if m["upstream"]["commit"] != PROVENANCE["commit"]:
        raise ValueError("Unexpected upstream revision")
    path = UPSTREAM / m["upstream_config"]
    if (design / "upstream_config.json").read_bytes() != path.read_bytes():
        raise ValueError("Upstream config was modified")
    original = json.loads(path.read_text())
    expected_config, changes = effective_config(design.name, original)
    config = json.loads((design / "config.json").read_text())
    if config != expected_config or m["config_adjustments"] != changes:
        raise ValueError("Effective config differs from documented transformations")
    arrays = interface(design)
    if arrays != m["arrays"] or arrays != {
        d["name"]: d["dims"] for d in config["drams"]
    }:
        raise ValueError("Interface, manifest, and config disagree")
    if (
        set(m["outputs"]) != set(config["output_dram_names"])
        or set(m["inputs"]) != arrays.keys() - m["outputs"].keys()
    ):
        raise ValueError("Input/output coverage differs from config")
    for filename, checksum in m["sha256"].items():
        if hashlib.sha256((design / filename).read_bytes()).hexdigest() != checksum:
            raise ValueError(filename + ": checksum mismatch")
    expected_inputs = make_inputs(config, m["seed"])
    inputs = {}
    for key, filename in m["inputs"].items():
        value = np.loadtxt(design / filename).reshape(arrays[key])
        if not np.array_equal(value, expected_inputs[key]):
            raise ValueError(filename + ": differs from seeded generation")
        inputs[key] = value
    reference = golden_outputs(config, inputs, m["domain"])
    checked = {}
    for key, filename in m["outputs"].items():
        value = np.loadtxt(design / filename).reshape(arrays[key])
        if not np.isfinite(value).all() or not np.allclose(
            value, reference[key], atol=1e-12, rtol=1e-14
        ):
            raise ValueError(filename + ": differs from float64 golden")
        checked[key] = {
            "count": int(value.size),
            "nonzero": int(np.count_nonzero(value)),
            "max_model_error": float(np.max(np.abs(value - reference[key]))),
        }
    extras = (
        {p.name for p in design.glob("*.txt")}
        - set(m["inputs"].values())
        - set(m["outputs"].values())
    )
    if extras:
        raise ValueError(f"Obsolete fixture files: {sorted(extras)}")
    if not m["functional_coverage_complete"]:
        raise ValueError("Incomplete functional coverage")
    return {"status": "pass", "outputs": checked, "config_adjustments": changes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument(
        "--allow-subset",
        action="store_true",
        help="Audit a deliberately selected development subset",
    )
    args = parser.parse_args()
    configs, _ = catalog()
    designs = {p.parent.name: p.parent for p in args.root.glob("*/top.cpp")}
    report = {}
    suite_path = args.root / "suite.json"
    if not suite_path.is_file():
        report["_suite"] = {"status": "fail", "error": "Missing suite.json"}
    else:
        suite = json.loads(suite_path.read_text())
        if (
            set(suite["designs"]) != set(designs)
            or suite["upstream"]["commit"] != PROVENANCE["commit"]
        ):
            report["_suite"] = {
                "status": "fail",
                "error": "Suite index disagrees with dataset",
            }
    if not designs or (not args.allow_subset and set(designs) != set(configs)):
        report["_coverage"] = {
            "status": "fail",
            "missing": sorted(configs.keys() - designs.keys()),
            "extra": sorted(designs.keys() - configs.keys()),
        }
    for filename, checksum in PROVENANCE["files"].items():
        if hashlib.sha256((UPSTREAM / filename).read_bytes()).hexdigest() != checksum:
            report["_upstream"] = {
                "status": "fail",
                "error": "Vendored upstream file modified: " + filename,
            }
    for name, design in sorted(designs.items()):
        try:
            report[name] = audit_design(design)
        except (OSError, ValueError, KeyError) as exc:
            report[name] = {"status": "fail", "error": str(exc)}
        print(name + ": " + report[name]["status"], flush=True)
    args.report.write_text(json.dumps(report, indent=2) + "\n")
    raise SystemExit(0 if all(v["status"] == "pass" for v in report.values()) else 1)


if __name__ == "__main__":
    main()
