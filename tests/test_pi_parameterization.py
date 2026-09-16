import json
import shutil
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from jinja2 import UndefinedError
from jinja2.sandbox import SecurityError
from llm_openrouter import OpenRouterChat

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools
from hls_eval.eval_agent_pi import eval_agent_pi_paramaterized as module
from hls_eval.eval_agent_pi.eval_agent_pi import PiAgentRunResult
from hls_eval.flow_parameterization.flow_parameterization import (
    DesignSpaceExplicit,
    JinjaParamaterizationFlow,
)
from hls_eval.tools import ExecutionData, ToolDataOutput


KERNEL = """#include "kernel.h"
int kernel(int x) {
#pragma HLS INTERFACE ap_ctrl_hs port=return
    return helper(x);
}
"""
TEMPLATE = """#include "kernel.h"
int kernel(int x) {
#pragma HLS INTERFACE ap_ctrl_hs port=return
{% if pipeline %}
#pragma HLS PIPELINE II=1
{% endif %}
    return helper(x);
}
"""


def output(code=0, metrics=None, timeout=False):
    return ToolDataOutput(ExecutionData(code, "", "", 0, 1, 1, timeout), metrics)


def metrics(latency=10, lut=10):
    return dict(zip(module.PARETO_OBJECTIVES, (latency, lut, 20, 0, 0, 0)))


@pytest.fixture
def pools():
    value = EvalThreadPools(1, 1, 1, 1)
    yield value
    value.shutdown()


@pytest.fixture
def design(tmp_path):
    original = tmp_path / "original"
    original.mkdir()
    (original / "kernel.cpp").write_text(KERNEL)
    (original / "helper.cpp").write_text(
        '#include "kernel.h"\nint helper(int x) { return x + 1; }\n'
    )
    (original / "kernel.h").write_text("int kernel(int);\nint helper(int);\n")
    (original / "extra.hpp").write_text("// another immutable header\n")
    (original / "kernel_tb.cpp").write_text("""#include "kernel.h"
#include <fstream>
int main() {
    std::ifstream input("input.txt");
    int x = 0;
    if (!(input >> x)) return 2;
    return kernel(x) == x + 1 ? 0 : 1;
}
""")
    (original / "input.txt").write_text("7\n")
    (original / "top.txt").write_text("kernel\n")
    (original / "kernel_description.md").write_text("Add one to the input.\n")
    (original / "hls_eval_config.toml").write_text(
        'tags = ["test"]\ntb_data = ["input.txt"]\n'
    )
    return original


@pytest.fixture
def evaluator(tmp_path):
    csim = Mock()
    csim.vitis_hls_path = tmp_path / "vendor"
    csim.run.return_value = (output(), output())
    synth = Mock()
    synth.run.return_value = output(metrics=metrics())
    return module.HLSParameterizationAgentEvaluatorPi(
        csim,
        synth,
        tmp_path / "results",
        compile_timeout=15,
        csim_timeout=5,
    )


def submission(design, tmp_path):
    agent = tmp_path / "agent"
    shutil.copytree(design, agent)
    (agent / "kernel.cpp").write_text(TEMPLATE)
    (agent / "design_space.jsonl").write_text(
        '{"pipeline": false}\n{"pipeline": true}\n'
    )
    return agent


def evaluate(evaluator, design, agent, tmp_path, pools):
    work = tmp_path / "evaluation"
    work.mkdir()
    return evaluator._evaluate_sample(
        design,
        agent,
        work,
        ["helper.cpp", "kernel.cpp"],
        "kernel_tb.cpp",
        "kernel",
        pools,
    )


requires_clang = pytest.mark.skipif(
    shutil.which("clang++") is None, reason="Clang unavailable"
)


@requires_clang
def test_complete_design_passes_with_csim_and_synth_tools(
    evaluator, design, tmp_path, pools
):
    agent = submission(design, tmp_path)
    evaluator.vitis_hls_tool.run.side_effect = [
        output(metrics=metrics(20, 20)),
        output(metrics=metrics(10, 20)),
        output(metrics=metrics(20, 10)),
    ]
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert result["passed"]
    assert result["baseline"]["passed"]
    assert all(
        p["testbench_passed"] and p["interface_preserved"] for p in result["points"]
    )
    assert result["summary"]["unique_pareto_point_indices"] == [0, 1]
    assert result["summary"]["points_dominating_baseline"] == [0, 1]
    assert (design / "kernel.cpp").read_text() == KERNEL
    for call in evaluator.vitis_hls_tool.run.call_args_list:
        assert not any(p.name.endswith("_tb.cpp") for p in call.args[1])
        assert call.kwargs["hls_top_function"] == "kernel"
        assert call.kwargs["hls_unsafe_math"] is True
        assert call.kwargs["hls_disable_auto_optimizations"] is True
    for call in evaluator.cpp_compiler_tool.run.call_args_list:
        assert any(p.name.endswith("_tb.cpp") for p in call.args[1])
        assert call.kwargs["hls_top_function"] == "kernel"
        assert call.kwargs["timeout"] == evaluator.csim_timeout
    assert evaluator.cpp_compiler_tool.run.call_count == 3
    assert (tmp_path / "evaluation/points/point__1/result.json").is_file()
    point_result = json.loads(
        (tmp_path / "evaluation/points/point__1/result.json").read_text()
    )
    assert point_result["c_compile_out"]["data_execution"]["return_code"] == 0
    assert point_result["c_run_out"]["data_execution"]["return_code"] == 0
    assert "data_tool" in point_result["vitis_hls_tool_out"]


@pytest.mark.parametrize(
    "name", ["kernel_tb.cpp", "kernel.h", "extra.hpp", "input.txt", "top.txt"]
)
def test_rejects_modified_protected_files(evaluator, design, tmp_path, pools, name):
    agent = submission(design, tmp_path)
    (agent / name).write_text("modified")
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert name in result["modified_protected_files"]
    evaluator.vitis_hls_tool.run.assert_not_called()
    evaluator.cpp_compiler_tool.run.assert_not_called()


@pytest.mark.parametrize(
    "jsonl",
    [
        "",
        "{}\n",
        "[]\n{}",
        '{"x": null}\n{}',
        '{"x": []}\n{}',
        '{"x": NaN}\n{}',
        '{"x": Infinity}\n{}',
        "{}\n{}",
        "bad json\n{}",
    ],
)
def test_invalid_design_space_is_serializable_failure(
    evaluator, design, tmp_path, pools, jsonl
):
    agent = submission(design, tmp_path)
    (agent / "design_space.jsonl").write_text(jsonl)
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["can_parse_output"]
    assert result["submission_error"]
    json.dumps(result)
    evaluator.vitis_hls_tool.run.assert_not_called()
    evaluator.cpp_compiler_tool.run.assert_not_called()


def test_design_space_limit_does_not_silently_truncate(evaluator, design, tmp_path):
    agent = submission(design, tmp_path)
    evaluator.max_design_points = 2
    (agent / "design_space.jsonl").write_text('{"x": 1}\n{"x": 2}\n{"x": 3}')
    checks, _, _ = evaluator._read_submission(
        design, agent, ["helper.cpp", "kernel.cpp"], "kernel_tb.cpp"
    )
    assert "got 3" in checks["submission_error"]


@requires_clang
def test_render_failure_does_not_abort_later_points(evaluator, design, tmp_path, pools):
    agent = submission(design, tmp_path)
    (agent / "design_space.jsonl").write_text('{}\n{"pipeline": true}')
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert not result["points"][0]["render_success"]
    assert "UndefinedError" in result["points"][0]["error"]
    assert result["points"][1]["passed"]
    assert evaluator.vitis_hls_tool.run.call_count == 2


@requires_clang
@pytest.mark.parametrize(
    "csim_result,failed_field",
    [
        ((output(code=1), None), "compile_passed"),
        ((output(), output(code=1)), "testbench_passed"),
        ((output(), output(code=-1, timeout=True)), "testbench_passed"),
    ],
)
def test_csim_compile_and_testbench_failures(
    evaluator, design, tmp_path, pools, csim_result, failed_field
):
    agent = submission(design, tmp_path)
    evaluator.cpp_compiler_tool.run.return_value = csim_result
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert all(not point[failed_field] for point in result["points"])
    assert result["summary"]["n_metric_eligible"] == 0
    assert evaluator.vitis_hls_tool.run.call_count == 3


@requires_clang
def test_invalid_cpp_fails_interface_signature_check(evaluator, design, tmp_path, pools):
    agent = submission(design, tmp_path)
    (agent / "kernel.cpp").write_text(
        TEMPLATE.replace("return helper(x);", "this is not C++;")
    )
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert all(not point["clang_syntax_passed"] for point in result["points"])
    assert all(not point["interface_preserved"] for point in result["points"])


@requires_clang
def test_extra_top_overload_rejected_even_when_testbench_passes(
    evaluator, design, tmp_path, pools
):
    agent = submission(design, tmp_path)
    (agent / "kernel.cpp").write_text(
        TEMPLATE + "int kernel(float x) { return int(x) + 1; }\n"
    )
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert all(
        p["testbench_passed"] and not p["interface_preserved"] for p in result["points"]
    )
    assert not result["passed"]


@requires_clang
def test_interface_pragma_change_rejected(evaluator, design, tmp_path, pools):
    agent = submission(design, tmp_path)
    (agent / "kernel.cpp").write_text(TEMPLATE.replace("ap_ctrl_hs", "ap_ctrl_none"))
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert all(not p["interface_pragmas_preserved"] for p in result["points"])


@requires_clang
def test_identical_renderings_are_not_parameterization(
    evaluator, design, tmp_path, pools
):
    agent = submission(design, tmp_path)
    (agent / "kernel.cpp").write_text(KERNEL)
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert result["points"][1]["duplicate_of"] == 0
    assert result["summary"]["n_unique_renderings"] == 1


@requires_clang
def test_synthesis_exception_is_local_to_point(evaluator, design, tmp_path, pools):
    agent = submission(design, tmp_path)
    evaluator.vitis_hls_tool.run.side_effect = [
        output(metrics=metrics()),
        RuntimeError("missing report"),
        output(metrics=metrics()),
    ]
    result = evaluate(evaluator, design, agent, tmp_path, pools)
    assert not result["passed"]
    assert "missing report" in result["points"][0]["synthesis_error"]
    assert result["points"][1]["passed"]
    assert result["summary"]["pareto_point_indices"] == [1]


def test_pareto_excludes_failures_unknown_metrics_and_duplicate_outcomes():
    def point(index, latency, lut, passed=True):
        return {
            "point_index": index,
            "passed": passed,
            "vitis_hls_tool_out": {"data_tool": metrics(latency, lut)},
        }

    points = [
        point(0, 5, 20),
        point(1, 20, 5),
        point(2, 20, 20),
        point(3, 5, 20),
        point(4, 1, 1, False),
        point(5, None, 0),
        point(6, float("nan"), 0),
    ]
    summary = module.summarize_design_space(points, point(-1, 30, 30))
    assert summary["pareto_point_indices"] == [0, 1, 3]
    assert summary["unique_pareto_point_indices"] == [0, 1]
    assert summary["unique_pareto_fraction"] == 2 / 7
    assert summary["points_dominating_baseline"] == [0, 1, 2, 3]


def test_strict_jinja_is_opt_in():
    space = DesignSpaceExplicit([{}])
    assert JinjaParamaterizationFlow().preprocess({"x": "{{ missing }}"}, space) == [
        {"x": ""}
    ]
    with pytest.raises(UndefinedError):
        JinjaParamaterizationFlow(strict_undefined=True).preprocess(
            {"x": "{{ missing }}"}, space
        )


def test_agent_templates_cannot_access_python_internals():
    with pytest.raises(SecurityError):
        JinjaParamaterizationFlow(strict_undefined=True, sandboxed=True).preprocess(
            {"kernel.cpp": "{{ cycler.__init__.__globals__ }}"},
            DesignSpaceExplicit([{}]),
        )


@requires_clang
def test_pi_orchestration_multiple_samples(
    evaluator, design, tmp_path, pools, monkeypatch
):
    model = SimpleNamespace(name="test-model", llm=Mock(spec=OpenRouterChat))
    model.llm.key, model.llm.model_name = "test-key", "test-model"
    evaluator.n_samples = 2
    calls = []

    def run_agent(**kwargs):
        directory = kwargs["agent_run_dir"]
        assert (directory / "kernel.cpp").read_text() == KERNEL
        assert (directory / "helper.cpp").is_file()
        assert (directory / "input.txt").is_file()
        assert "csynth_design" in kwargs["prompt"]
        calls.append(directory)
        (directory / "kernel.cpp").write_text(TEMPLATE)
        (directory / "design_space.jsonl").write_text(
            '{"pipeline": false}\n{"pipeline": true}'
        )
        return PiAgentRunResult(0, "done", True, False, [], None, None)

    monkeypatch.setattr(module, "run_pi_agent", run_agent)
    evaluator.evaluate_design(BenchmarkCase(design, name="complete"), model, pools)
    results_file = next(evaluator.output_data_dir.rglob("all_eval_data.json"))
    results = json.loads(results_file.read_text())
    assert len(calls) == len(results) == 2
    assert all(value["passed"] for value in results.values())
    assert "test-key" not in results_file.read_text()


@pytest.mark.parametrize("failure", ["limit", "exception"])
def test_agent_failure_persists_results(evaluator, design, pools, monkeypatch, failure):
    model = SimpleNamespace(name="test-model", llm=Mock(spec=OpenRouterChat))
    model.llm.key, model.llm.model_name = "test-key", "test-model"

    def run_agent(**kwargs):
        if failure == "exception":
            raise RuntimeError("container unavailable")
        return PiAgentRunResult(1, "rate limit", False, True, [], None, None)

    monkeypatch.setattr(module, "run_pi_agent", run_agent)
    evaluator.evaluate_design(BenchmarkCase(design), model, pools)
    results = json.loads(
        next(evaluator.output_data_dir.rglob("single_eval_data.json")).read_text()
    )
    assert not results["passed"]
    evaluator.vitis_hls_tool.run.assert_not_called()
    evaluator.cpp_compiler_tool.run.assert_not_called()
