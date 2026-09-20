import json
from types import SimpleNamespace
from unittest.mock import Mock

import pytest
from llm_openrouter import OpenRouterChat

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools
from hls_eval.eval_agent_pi import eval_agent_pi_paramaterized as module
from hls_eval.eval_agent_pi.eval_agent_pi import PiAgentRunResult
from test_pi_parameterization import KERNEL, TEMPLATE, metrics, output


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
    (original / "kernel_tb.cpp").write_text(
        '#include "kernel.h"\n#include <fstream>\nint main() {\n'
        '    std::ifstream input("input.txt");\n    int x = 0;\n'
        "    if (!(input >> x)) return 2;\n"
        "    return kernel(x) == x + 1 ? 0 : 1;\n}\n"
    )
    (original / "input.txt").write_text("7\n")
    (original / "top.txt").write_text("kernel\n")
    (original / "kernel_description.md").write_text("Add one to the input.\n")
    (original / "hls_eval_config.toml").write_text(
        'tags = ["test"]\ntb_data = ["input.txt"]\n'
    )
    return original


def _write_log_and_return(build_name_prefix, log_text, result):
    """Stand-in for a real tool run: writes the vitis_hls.log a real run would
    leave under build_dir/<prefix>variant/, then returns the canned result."""

    def run(build_dir, *args, **kwargs):
        log_dir = build_dir / f"{build_name_prefix}{kwargs['build_name']}"
        log_dir.mkdir(parents=True, exist_ok=True)
        (log_dir / "vitis_hls.log").write_text(
            f"{log_text} {build_dir.parents[2].name}/{build_dir.parent.name}"
        )
        return result

    return run


def test_collect_point_artifacts_copies_logs_only_for_rendered_points(tmp_path):
    iter_dir = tmp_path / "iter"
    agent_dir = tmp_path / "agent"
    agent_dir.mkdir()
    for index in (0, 1):
        build = iter_dir / "points" / f"point__{index}" / "build"
        (build / "vitis_hls_csim_tool__variant").mkdir(parents=True)
        (build / "vitis_hls_csim_tool__variant" / "vitis_hls.log").write_text(
            f"csim {index}"
        )
        (build / "vitis_hls_synth_tool__variant").mkdir(parents=True)
        (build / "vitis_hls_synth_tool__variant" / "vitis_hls.log").write_text(
            f"synth {index}"
        )
        (build / "vitis_hls_synth_tool__variant" / "report.rpt").write_text("rpt")

    module._collect_point_artifacts(
        iter_dir,
        agent_dir,
        [
            {"point_index": 0, "render_success": True},
            {"point_index": 1, "render_success": False},
            {"point_index": 2, "render_success": True},
        ],
    )

    artifacts = agent_dir / "previous_design_artifacts"
    assert (artifacts / "point__0" / "vitis_hls_csim.log").read_text() == "csim 0"
    assert (artifacts / "point__0" / "vitis_hls_synth.log").read_text() == "synth 0"
    assert sorted(p.name for p in (artifacts / "point__0").iterdir()) == [
        "vitis_hls_csim.log",
        "vitis_hls_synth.log",
    ]
    assert not (artifacts / "point__1").exists()
    assert not (artifacts / "point__2").exists()


@pytest.mark.skipif(
    __import__("shutil").which("clang++") is None, reason="Clang unavailable"
)
def test_artifacts_carry_forward_only_from_the_immediately_preceding_iteration(
    design, tmp_path, pools, monkeypatch
):
    csim = Mock()
    csim.vitis_hls_path = tmp_path / "vendor"
    csim.run.side_effect = _write_log_and_return(
        "vitis_hls_csim_tool__", "csim log", (output(), output())
    )
    synth = Mock()
    synth.run.side_effect = _write_log_and_return(
        "vitis_hls_synth_tool__", "synth log", output(metrics=metrics())
    )
    evaluator = module.HLSParameterizationIterativeAgentEvaluatorPi(
        csim, synth, tmp_path / "results", n_iters=3, compile_timeout=15
    )
    model = SimpleNamespace(name="test-model", llm=Mock(spec=OpenRouterChat))
    model.llm.key, model.llm.model_name = "test-key", "test-model"

    seen_at_agent_start: list[dict[str, str]] = []

    def run_agent(**kwargs):
        directory = kwargs["agent_run_dir"]
        artifacts = directory / "previous_design_artifacts"
        seen_at_agent_start.append(
            {
                p.relative_to(artifacts).as_posix(): p.read_text()
                for p in sorted(artifacts.rglob("*.log"))
            }
            if artifacts.exists()
            else {}
        )
        (directory / "kernel.cpp").write_text(TEMPLATE)
        (directory / "design_space.jsonl").write_text(
            '{"pipeline": false}\n{"pipeline": true}'
        )
        return PiAgentRunResult(0, "done", True, False, [], None, None)

    monkeypatch.setattr(module, "run_pi_agent", run_agent)
    evaluator.evaluate_design(BenchmarkCase(design, name="complete"), model, pools)

    def expected(iteration):
        return {
            f"point__{i}/vitis_hls_{kind}.log": f"{kind} log iteration__{iteration}/point__{i}"
            for i in (0, 1)
            for kind in ("csim", "synth")
        }

    assert seen_at_agent_start == [{}, expected(0), expected(1)]

    results = json.loads(
        next(evaluator.output_data_dir.rglob("all_eval_data.json")).read_text()
    )
    assert results["0"]["passed"]
    assert "previous_design_artifacts/point__<index>" in (
        results["0"]["iterations"][1]["prompt"]
    )
    assert "previous_design_artifacts" not in results["0"]["iterations"][0]["prompt"]
