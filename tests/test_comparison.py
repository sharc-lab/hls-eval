import json
from pathlib import Path
from unittest.mock import Mock

import pytest

from hls_eval.comparison import (
    compare_dump,
    functional_passed,
    recorded_functional_result,
    run_checked_csim,
)
from hls_eval.data import BenchmarkCase
from hls_eval.tools import ExecutionData, ToolDataOutput


def output(stdout="", stderr="", rc=0, timeout=False):
    return ToolDataOutput(ExecutionData(rc, stdout, stderr, 0, 1, 1, timeout), None)


@pytest.mark.parametrize(
    "actual,expected,passed",
    [
        ("A 1 2 END", "A 1 2 END", True),
        ("A 1.0000005 2 END", "A 1 2 END", True),
        ("A 1.00001 2 END", "A 1 2 END", False),
        ("A 0.0000000005 2 END", "A 0 2 END", True),
        ("A nan 2 END", "A 1 2 END", False),
        ("A inf 2 END", "A 1 2 END", False),
        ("A 1 2 END", "A nan 2 END", False),
        ("A 1 2", "A 1 2 END", False),
        ("A 1 2 END extra", "A 1 2 END", False),
        ("B 1 2 END", "A 1 2 END", False),
        ("A 1 3 END", "A 1 2 END", False),
    ],
)
def test_numeric_dump(actual, expected, passed):
    assert compare_dump(actual, expected, kind="numeric_dump")["passed"] is passed


def test_exact_bits_and_integer_tokens_are_not_rounded():
    assert not compare_dump("x 0x7ffffffe", "x 0x7fffffff", kind="exact_tokens")[
        "passed"
    ]
    assert not compare_dump("1000000001", "1000000000", kind="exact_tokens")["passed"]
    assert compare_dump("0x80000000 0x1", "0x80000000 0x1", kind="exact_tokens")[
        "passed"
    ]
    with pytest.raises(ValueError, match="empty"):
        compare_dump("", "", kind="exact_tokens")


@pytest.fixture
def case(tmp_path):
    directory = tmp_path / "case"
    directory.mkdir()
    for name, text in {
        "top.txt": "top",
        "top.cpp": "int top(){return 7;}",
        "top.h": "int top();",
        "top_tb.cpp": "int main(){return 0;}",
        "kernel_description.md": "Return seven.",
        "hls_eval_config.toml": '[comparison]\nkind="numeric_dump"\nchannel="stderr"\n'
        'token_count=3\ncompletion_markers=["END"]\n',
    }.items():
        (directory / name).write_text(text)
    return BenchmarkCase(directory)


def invoke(case, tmp_path, reference, candidate):
    tool = Mock(vitis_hls_path=Path("/sdk"))
    tool.run.side_effect = [(output(), reference), (output(), candidate)]
    _, run = run_checked_csim(
        tool, case, tmp_path / "build", case.source_files, hls_compiler_defines=["N=4"]
    )
    return run, tool


@pytest.mark.parametrize(
    "actual,passed",
    [("v 7 END", True), ("v 8 END", False), ("v nan END", False), ("v 7", False)],
)
def test_checked_csim_uses_full_stderr_and_preserves_rc(case, tmp_path, actual, passed):
    run, tool = invoke(
        case,
        tmp_path,
        output(stderr="v 7 END"),
        output(stdout="v 7 END", stderr=actual),
    )
    assert functional_passed(run) is passed
    assert run.data_execution.return_code == 0
    check = run.data_tool["functional_check"]
    assert check["status"] == ("passed" if passed else "failed")
    evidence = json.loads(Path(check["reference_evidence"]).read_text())
    assert evidence["run"]["data_execution"]["stderr"] == "v 7 END"
    assert evidence["csim_options"]["hls_compiler_defines"] == ["N=4"]
    assert "top.cpp" in evidence["files_sha256"]
    assert tool.run.call_count == 2


@pytest.mark.parametrize(
    "reference",
    [
        None,
        output(rc=1),
        output(timeout=True),
        output(stderr=""),
        output(stderr="v 7"),
        output(stderr="v 7 STOP"),
        output(stderr="v nan END"),
    ],
)
def test_unusable_reference_is_fixture_error(case, tmp_path, reference):
    run, _ = invoke(case, tmp_path, reference, output(stderr="v 7 END"))
    assert not functional_passed(run)
    assert run.data_tool["functional_check"]["status"] == "fixture_error"
    assert run.data_tool["functional_check"]["passed"] is None


@pytest.mark.parametrize("reference_failed", [False, True])
def test_compile_failure_keeps_functional_evidence(case, tmp_path, reference_failed):
    tool = Mock(vitis_hls_path=Path("/sdk"))
    tool.run.side_effect = [
        (output(rc=1), None)
        if reference_failed
        else (output(), output(stderr="v 7 END")),
        (output(rc=1), None),
    ]
    compiled, run = run_checked_csim(tool, case, tmp_path / "build", case.source_files)
    assert run is None
    check = compiled.data_tool["functional_check"]
    assert check["status"] == ("fixture_error" if reference_failed else "failed")
    assert check["passed"] is (None if reference_failed else False)


def test_undeclared_case_is_unverified(case, tmp_path):
    (case.design_dir / "hls_eval_config.toml").write_text('tags=["test"]')
    tool = Mock()
    tool.run.return_value = (output(), output())
    _, run = run_checked_csim(tool, case, tmp_path / "build", case.source_files)
    assert run.data_tool["functional_check"]["status"] == "unverified"
    assert not functional_passed(run)
    assert tool.run.call_count == 1


def test_self_checker_uses_trusted_tb(case, tmp_path):
    (case.design_dir / "hls_eval_config.toml").write_text(
        '[comparison]\nkind="exit_code"'
    )
    changed_tb = tmp_path / "top_tb.cpp"
    changed_tb.write_text("int main(){return 0;}")
    tool = Mock()
    tool.run.return_value = (output(), output(rc=1))
    _, run = run_checked_csim(
        tool, case, tmp_path / "build", [case.kernel_fp, changed_tb]
    )
    assert not functional_passed(run)
    assert changed_tb not in tool.run.call_args.args[1]
    assert case.tb_file in tool.run.call_args.args[1]


def test_missing_reference_data_is_fixture_error(case, tmp_path):
    config = case.design_dir / "hls_eval_config.toml"
    config.write_text('tb_data=["missing.dat"]\n' + config.read_text())
    tool = Mock(vitis_hls_path=Path("/sdk"))
    tool.run.return_value = (output(), output(stderr="v 7 END"))
    _, run = run_checked_csim(tool, case, tmp_path / "build", case.source_files)
    assert run.data_tool["functional_check"]["status"] == "fixture_error"
    assert (
        recorded_functional_result(
            {"functional_check": run.data_tool["functional_check"]}
        )
        is None
    )
    assert tool.run.call_count == 1


def test_execution_only_historical_record_is_not_functional_success():
    assert (
        recorded_functional_result(
            {"c_run_out": {"data_execution": {"return_code": 0}}}
        )
        is None
    )


@pytest.mark.parametrize(
    "record",
    [
        {"can_parse_output": False},
        {"c_compile_out": {"data_execution": {"return_code": 1}}},
        {"c_run_out": {"data_execution": {"return_code": 1}}},
        {"c_run_out": {"data_execution": {"return_code": 0, "timeout": True}}},
    ],
)
def test_known_execution_failures_are_failures(record):
    assert recorded_functional_result(record) is False


def test_parameterized_consumer_rejects_wrong_dump_without_clang(case, tmp_path):
    import shutil

    from hls_eval.eval import EvalThreadPools
    from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized import (
        HLSParameterizationAgentEvaluatorPi,
    )

    candidate = tmp_path / "candidate" / "design"
    shutil.copytree(case.design_dir, candidate)
    (candidate / "top.cpp").write_text("int top(){return 8;}")
    csim = Mock(vitis_hls_path=Path("/sdk"))
    csim.run.side_effect = [
        (output(), output(stderr="v 7 END")),
        (output(), output(stderr="v 8 END")),
    ]
    synth = Mock()
    synth.run.return_value = output()
    evaluator = HLSParameterizationAgentEvaluatorPi(csim, synth, tmp_path / "result")
    evaluator._check_interface_signature = Mock(
        return_value={
            "clang_syntax_passed": True,
            "top_signatures": [{"type": "int ()"}],
        }
    )
    pools = EvalThreadPools(1, 1, 1, 1)
    try:
        result = evaluator._evaluate_variant(
            candidate,
            ["top.cpp"],
            "top_tb.cpp",
            "top",
            pools,
            reference_dir=case.design_dir,
        )
    finally:
        pools.shutdown()
    assert result["compile_passed"]
    assert not result["testbench_passed"]
    assert result["functional_check"]["reason"] == "output mismatch"
    assert not result["passed"]
    assert case.kernel_fp in csim.run.call_args_list[0].args[1]
    assert candidate / "top.cpp" not in csim.run.call_args_list[0].args[1]


def test_statistics_leave_unverified_functional_rates_unavailable():
    import pandas as pd

    from hls_eval_experiments.exp_utils import compute_pass_rates

    data = pd.DataFrame(
        [
            {
                "eval_id": "e",
                "model_name": "m",
                "benchmark_case_name": "b",
                "pass_parse": True,
                "pass_compile": True,
                "pass_synth": True,
                "pass_tb": True,
                "pass_tb_and_synth": True,
            },
            {
                "eval_id": "e",
                "model_name": "m",
                "benchmark_case_name": "b",
                "pass_parse": True,
                "pass_compile": True,
                "pass_synth": True,
                "pass_tb": None,
                "pass_tb_and_synth": None,
            },
        ]
    )
    rates = compute_pass_rates(data, ks=[1])
    assert rates.loc[rates.metric_name == "pass_tb", "pass_rate"].isna().all()
    assert rates.loc[rates.metric_name == "pass_tb_and_synth", "pass_rate"].isna().all()
    assert rates.loc[rates.metric_name == "pass_compile", "pass_rate"].iloc[0] == 1.0
