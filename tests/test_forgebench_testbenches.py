"""Functional checks for base-config generation and strict golden comparison."""

from __future__ import annotations
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pytest

TOOLS = Path(__file__).resolve().parents[1] / "design_gen_scripts" / "forgebench"
sys.path.insert(0, str(TOOLS))
import generate as forge_generate  # noqa: E402
from reference import conv, llm  # noqa: E402
from reference.activations import softmax  # noqa: E402


def test_float_reference_does_not_truncate_or_wrap():
    arrays = {
        "x": np.array([[16.0, 16.0], [1 / 2048, 1 / 2048]]),
        "w": np.array([[1.0, 1.0]]),
        "out": np.zeros((2, 1)),
    }
    op = {
        "dims": [2, 2, 1],
        "func_info": ["matmul_template.cpp", False],
        "args": ["x", "w", "out"],
    }
    llm._op_matmul(op, arrays)
    np.testing.assert_array_equal(arrays["out"], [[32.0], [2 / 2048]])
    arrays["w"][:] = 0.75
    llm._op_matmul(op, arrays)
    assert arrays["out"][1, 0] == 1.5 / 2048


def test_softmax_is_finite_and_normalized():
    y = softmax(np.array([[1000.0, 1001.0, 999.0]]))
    assert np.isfinite(y).all()
    np.testing.assert_allclose(y.sum(axis=1), 1)


def test_convolution_padding_orientation_and_extended_output():
    arrays = {
        "x": np.arange(1, 10, dtype=float).reshape(1, 3, 3),
        "w": np.zeros((1, 1, 3, 3)),
        "b": np.array([0.25]),
        "out": np.zeros((1, 4, 4)),
    }
    arrays["w"][0, 0, 0, 1] = 0.5
    op = {
        "dims": [1, 1, 3, 3, 4, 4, 3, 1, 1],
        "func_info": ["conv_template.cpp", "conv2d", True],
        "args": ["x", "w", "b", "out"],
    }
    conv._op_conv(op, arrays)
    np.testing.assert_array_equal(
        arrays["out"],
        [
            [
                [0.25, 0.25, 0.25, 0.25],
                [0.75, 1.25, 1.75, 0.25],
                [2.25, 2.75, 3.25, 0.25],
                [3.75, 4.25, 4.75, 0.25],
            ]
        ],
    )


def test_attention_uniform_scores_average_values():
    arrays = {
        "x": np.array([[1.0, 2.0], [3.0, 4.0]]),
        "q": np.zeros((2, 2)),
        "k": np.zeros((2, 2)),
        "v": np.eye(2),
        "out": np.zeros((2, 2)),
    }
    op = {
        "dims": [2, 2, 1, 2],
        "func_info": ["grouped_mha_rope_template.cpp", False],
        "args": ["x", "q", "k", "v", "out", "1"],
    }
    llm._op_mha(op, arrays)
    np.testing.assert_array_equal(arrays["out"], [[2.0, 3.0], [2.0, 3.0]])


def test_reference_rejects_bounds_and_uninitialized_reads():
    with pytest.raises(ValueError, match="exceeds"):
        conv._read({"a": np.ones(8)}, "a", (9,))
    with pytest.raises(ValueError, match="exceeds"):
        conv._write({"a": np.ones(8)}, "a", np.ones(9))
    with pytest.raises(ValueError, match="uninitialized"):
        conv._read({"a": np.full(8, np.nan)}, "a", (8,))


@pytest.fixture(scope="module")
def harness(tmp_path_factory):
    if not shutil.which("g++"):
        pytest.skip("g++ is required for comparator checks")
    work = tmp_path_factory.mktemp("forge_comparator")
    source = work / "test.cpp"
    source.write_text(r"""
#include "tb_support.h"
int main(int argc, char **argv) {
    try {
        double actual[2][2];
        const std::vector<double> expected = forge_tb::read("golden.txt", 4);
        forge_tb::poison(actual, expected);
        if (argc == 1) forge_tb::load(actual, "actual.txt", 4);
        return forge_tb::check(actual, expected, "matrix", "dump.txt") ? 0 : 1;
    } catch (const std::exception &) { return 2; }
}
""")
    exe = work / "test"
    subprocess.run(
        ["g++", "-std=c++14", "-I", str(TOOLS), str(source), "-o", str(exe)], check=True
    )
    return exe


def run_harness(exe, work, actual="1 2 3 4", golden="1 2 3 4", poison=False):
    (work / "actual.txt").write_text(actual)
    (work / "golden.txt").write_text(golden)
    return subprocess.run(
        [str(exe)] + (["poison"] if poison else []),
        cwd=work,
        capture_output=True,
        text=True,
    )


def test_comparator_accepts_epsilon_and_rejects_corrupted_output(harness, tmp_path):
    assert run_harness(harness, tmp_path, actual="1.000999 2 3 4").returncode == 0
    assert run_harness(harness, tmp_path, actual="1.001001 2 3 4").returncode == 1
    assert run_harness(harness, tmp_path, actual="1.0015 2 3 4").returncode == 1
    assert (
        run_harness(
            harness, tmp_path, actual="0.001 2 3 4", golden="0 2 3 4"
        ).returncode
        == 0
    )
    failed = run_harness(harness, tmp_path, actual="1 2 3 4.01")
    assert failed.returncode == 1
    assert "matrix[3]" in failed.stderr
    assert "1/4 mismatches" in failed.stdout
    assert run_harness(harness, tmp_path, golden="1 2 3 5").returncode == 1


def test_unwritten_output_cannot_pass(harness, tmp_path):
    assert run_harness(harness, tmp_path, poison=True).returncode == 1


@pytest.mark.parametrize(
    "bad", ["1 2 3", "1 2 3 4 5", "1 2 NaN 4", "1 2 inf 4", "1 2 3 nope"]
)
@pytest.mark.parametrize("target", ["actual", "golden"])
def test_bad_fixture_is_an_error(harness, tmp_path, bad, target):
    assert run_harness(harness, tmp_path, **{target: bad}).returncode == 2


def test_missing_fixture_is_an_error(harness, tmp_path):
    assert subprocess.run([str(harness)], cwd=tmp_path).returncode == 2


def generate_one(root, name="mult_op_p1"):
    subprocess.run(
        [
            sys.executable,
            str(TOOLS / "generate.py"),
            "--root",
            str(root),
            "--design",
            name,
        ],
        check=True,
        capture_output=True,
    )
    return root / name


def test_generation_is_deterministic_and_replaces_bad_fixtures(tmp_path):
    design = generate_one(tmp_path)
    before = {p.name: p.read_bytes() for p in design.iterdir() if p.is_file()}
    for path in design.glob("*.txt"):
        path.write_text("invalid legacy data")
    (design / "BRAM_obsolete.txt").write_text("obsolete")
    (design / "DRAM_4_output.txt").write_text("obsolete")
    generate_one(tmp_path)
    assert before == {p.name: p.read_bytes() for p in design.iterdir() if p.is_file()}
    assert (design / "DRAM_4.golden.txt").exists()
    assert "golden_DRAM_4" in (design / "tb_top.cpp").read_text()


@pytest.mark.parametrize("name", ["testing_impl", "testing_unroll"])
def test_scalar_output_has_a_real_input_dependent_dot_product(name):
    path, original = forge_generate.catalog()[0][name]
    config, changes = forge_generate.effective_config(name, original)
    assert changes
    data = forge_generate.make_inputs(config, 42)
    result = forge_generate.golden_outputs(config, data, "gemm")
    expected = data["DRAM_5"][:16] @ data["DRAM_10"][:16] + data["DRAM_11"][0]
    assert result["DRAM_12"][0] == expected
    data["DRAM_11"][0] += 1
    updated = forge_generate.golden_outputs(config, data, "gemm")
    assert updated["DRAM_12"][0] == expected + 1
    assert json.loads(path.read_text()) == original


def test_fixture_audit_rejects_modified_data(tmp_path):
    design = generate_one(tmp_path)
    cmd = [
        sys.executable,
        str(TOOLS / "audit_fixtures.py"),
        "--root",
        str(tmp_path),
        "--allow-subset",
        "--report",
        str(tmp_path / "audit.json"),
    ]
    assert subprocess.run(cmd, capture_output=True).returncode == 0
    values = np.loadtxt(design / "DRAM_4.golden.txt")
    values[0] += 1
    np.savetxt(design / "DRAM_4.golden.txt", values)
    assert subprocess.run(cmd, capture_output=True).returncode == 1


def test_all_base_configs_are_accounted_for_and_upstream_is_pristine():
    configs, excluded = forge_generate.catalog()
    assert len(configs) == 50
    assert set(excluded) == {"conv/test_case_configs/conv_variable.json"}
    for filename, checksum in forge_generate.PROVENANCE["files"].items():
        assert (
            hashlib.sha256(
                (forge_generate.UPSTREAM / filename).read_bytes()
            ).hexdigest()
            == checksum
        )


def test_required_full_suite_audit_rejects_missing_designs(tmp_path):
    generate_one(tmp_path)
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "audit_fixtures.py"),
            "--root",
            str(tmp_path),
            "--report",
            str(tmp_path / "audit.json"),
        ],
        capture_output=True,
    )
    assert result.returncode == 1
    assert json.loads((tmp_path / "audit.json").read_text())["_coverage"]["missing"]


def test_unwritten_values_cannot_equal_poison(harness, tmp_path):
    assert (
        run_harness(harness, tmp_path, golden="-7 -16 15 0", poison=True).returncode
        == 1
    )


@pytest.mark.parametrize(
    "name,channels",
    [("resnet50_block3_downsample", 1024), ("resnet50_block4_downsample", 2048)],
)
def test_resnet_downsample_computes_and_stores_all_output_channels(name, channels):
    _, original = forge_generate.catalog()[0][name]
    config, changes = forge_generate.effective_config(name, original)
    for key in ["matrix_add", "activation_3", "store"]:
        assert config["ops"][key]["dims"][0] == channels
        assert original["ops"][key]["dims"][0] == channels // 2
    assert changes


def test_vector_matrix_reference_uses_all_64_inputs():
    _, original = forge_generate.catalog()[0]["vec_mtx_p2"]
    config, _ = forge_generate.effective_config("vec_mtx_p2", original)
    data = forge_generate.make_inputs(config, 42)
    expected = data["DRAM_1"].T @ data["DRAM_2"]
    actual = forge_generate.golden_outputs(config, data, "gemm")["DRAM_4"]
    np.testing.assert_array_equal(actual, expected)
    with pytest.raises(ValueError, match="uninitialized"):
        forge_generate.golden_outputs(original, data, "gemm")


def test_incremental_generation_keeps_complete_suite_index(tmp_path):
    generate_one(tmp_path, "mult_op_p1")
    generate_one(tmp_path, "mult_op_p2")
    generate_one(tmp_path, "mult_op_p1")
    assert json.loads((tmp_path / "suite.json").read_text())["designs"] == [
        "mult_op_p1",
        "mult_op_p2",
    ]


def test_validator_rejects_missing_testbench(tmp_path):
    root = tmp_path / "root"
    design = root / "missing"
    design.mkdir(parents=True)
    (design / "top.cpp").write_text("void top() {}")
    include = tmp_path / "include"
    include.mkdir()
    (include / "ap_fixed.h").write_text("")
    result = subprocess.run(
        [
            sys.executable,
            str(TOOLS / "validate.py"),
            "--root",
            str(root),
            "--hls-include",
            str(include),
            "--work-dir",
            str(tmp_path / "run"),
        ],
        capture_output=True,
        text=True,
    )
    assert result.returncode != 0
    assert "missing correctness manifests" in result.stderr
