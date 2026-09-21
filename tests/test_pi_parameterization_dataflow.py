import shutil
import stat
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from hls_eval.eval import EvalThreadPools
from hls_eval.eval_agent_pi import eval_agent_pi_paramaterized_dataflow as module
from hls_eval.eval_agent_pi.eval_agent_pi import run_pi_agent
from hls_eval.tools import VitisHLSSynthTool
from hls_eval.eval_agent_pi.lightningsim import (
    LightningSimTool,
    parse_lightningsim_output,
)
from test_pi_parameterization import TEMPLATE, design, metrics, output  # noqa: F401

Evaluator = module.HLSParameterizationIterativeDataflowAgentEvaluatorPi

LS_OUTPUT = """[23:14:25] [INFO] LightningSim: Simulation finished.
[      0-1597077] forward
\t[      0- 799509] node3
\t[ 159904-1597075] node1
"""

requires_clang = pytest.mark.skipif(
    shutil.which("clang++") is None, reason="Clang unavailable"
)


def ls_output(latency=None, *, deadlock=False, code=0, timeout=False):
    data = {module.LATENCY_KEY: latency, "deadlock": deadlock}
    return output(code=code, metrics=data, timeout=timeout)


@pytest.fixture
def vendor(tmp_path):
    root = tmp_path / "vendor" / "2024.1"
    (root / "include").mkdir(parents=True)
    return root


@pytest.fixture
def pools():
    value = EvalThreadPools(1, 1, 1, 3)
    yield value
    value.shutdown()


def make_evaluator(tmp_path, vendor, **kwargs):
    csim = Mock()
    csim.vitis_hls_path = vendor
    csim.run.return_value = (output(), output())
    synth = Mock()
    synth.vitis_hls_path = vendor
    kwargs.setdefault("agent_dataflow_tools", False)
    return Evaluator(
        csim,
        synth,
        tmp_path / "results",
        compile_timeout=15,
        csim_timeout=5,
        **kwargs,
    )


@pytest.fixture
def evaluator(tmp_path, vendor):
    value = make_evaluator(tmp_path, vendor)

    def synth_run(build_dir, sources, **kwargs):
        text = next(p for p in sources if Path(p).name == "kernel.cpp").read_text()
        # The Vitis estimate says the non-pipelined point is much faster;
        # LightningSim (below) says the opposite, so the frontier shows which
        # one is scored.
        pipelined = "PIPELINE" in text
        return output(
            metrics=metrics(100 if pipelined else 10, 30 if pipelined else 10)
        )

    def ls_run(solution_dir, timeout, log_path):
        value.ls_calls.append(Path(solution_dir))
        return ls_output(20 if "point__1" in str(solution_dir) else 50)

    value.ls_calls = []
    value.vitis_hls_tool.run.side_effect = synth_run
    value.lightningsim_tool = Mock()
    value.lightningsim_tool.run.side_effect = ls_run
    return value


def submission(design, tmp_path):  # noqa: F811
    agent = tmp_path / "agent"
    shutil.copytree(design, agent)
    (agent / "kernel.cpp").write_text(TEMPLATE)
    (agent / "design_space.jsonl").write_text(
        '{"pipeline": false}\n{"pipeline": true}\n'
    )
    return agent


def evaluate(evaluator, design, agent, tmp_path, pools):  # noqa: F811
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


# ---- LightningSim stage and Pareto scoring -----------------------------------


@requires_clang
def test_latency_comes_from_lightningsim_and_drives_the_frontier(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
):
    result = evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    assert result["passed"] and result["baseline"]["passed"]
    points = result["points"]
    assert [p["latency_lightningsim_cycles"] for p in points] == [50, 20]
    # The Vitis estimate is kept next to the LightningSim latency.
    data = points[1]["vitis_hls_tool_out"]["data_tool"]
    assert data["latency_lightningsim_cycles"] == 20
    assert data["latency_worst_cycles"] == 100
    assert result["summary"]["objectives"][0] == "latency_lightningsim_cycles"
    # By Vitis latency point 0 would dominate point 1; by LightningSim both stay.
    assert result["summary"]["pareto_point_indices"] == [0, 1]
    # LightningSim ran once per point and once for the baseline, on the
    # synthesized solution.
    assert len(evaluator.ls_calls) == 3
    assert all(
        call.match("build/vitis_hls_synth_tool__variant/*__proj/solution__synth")
        for call in evaluator.ls_calls
    )


@requires_clang
def test_synthesis_gets_the_testbench_and_its_data_files(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
):
    evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    for call in evaluator.vitis_hls_tool.run.call_args_list:
        assert sorted(p.name for p in call.kwargs["tb_files"]) == [
            "input.txt",
            "kernel_tb.cpp",
        ]


@requires_clang
@pytest.mark.parametrize(
    ("ls_result", "status", "reason"),
    [
        (ls_output(deadlock=True, code=1), "deadlock", "deadlock detected"),
        (ls_output(code=-1, timeout=True), "timeout", "timed out"),
        (ls_output(code=3), "failed", "exited with code 3"),
    ],
)
def test_lightningsim_failures_fail_the_point_with_a_reason(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
    ls_result,
    status,
    reason,
):
    evaluator.lightningsim_tool.run.side_effect = None
    evaluator.lightningsim_tool.run.return_value = ls_result
    result = evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    assert not result["passed"]
    point = result["points"][0]
    assert not point["passed"] and point["lightningsim_status"] == status
    assert module.LATENCY_KEY not in point
    assert result["summary"]["n_metric_eligible"] == 0
    text = module._format_previous_iteration_summary(
        {"agent_submitted": True, "can_parse_output": True, **result},
        objectives=module.DATAFLOW_OBJECTIVES,
        latency_keys=module.DATAFLOW_LATENCY_KEYS,
        extra_stage=module._lightningsim_stage_text,
        extra_stage_counts=(("lightningsim", "lightningsim_passed"),),
    )
    assert f"lightningsim FAILED ({reason}" in text
    assert "lightningsim 0/2" in text


@requires_clang
def test_synthesis_failure_skips_lightningsim(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
):
    evaluator.vitis_hls_tool.run.side_effect = None
    evaluator.vitis_hls_tool.run.return_value = output(code=1)
    result = evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    evaluator.lightningsim_tool.run.assert_not_called()
    point = result["points"][0]
    assert point["lightningsim_status"] == "skipped"
    assert point["lightningsim_skip_reason"] == "synthesis failed"
    assert not point["passed"]


@requires_clang
def test_lightningsim_exception_is_local_to_the_point(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
):
    def flaky(solution_dir, timeout, log_path):
        if "point__0" in str(solution_dir):
            raise RuntimeError("no such solution")
        return ls_output(20)

    evaluator.lightningsim_tool.run.side_effect = flaky
    result = evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    assert "no such solution" in result["points"][0]["lightningsim_error"]
    assert not result["points"][0]["passed"] and result["points"][1]["passed"]


def test_lightningsim_pool_matches_synth_pool_and_is_shut_down(tmp_path, vendor, pools):
    evaluator = make_evaluator(tmp_path, vendor)
    pool = evaluator._get_lightningsim_pool(pools)
    assert pool is evaluator._get_lightningsim_pool(pools)
    assert pool._max_workers == pools.n_jobs_pool_synth == 3
    evaluator._shutdown_lightningsim_pools()
    assert evaluator._ls_pools == {} and pool._shutdown


def test_artifacts_carry_lightningsim_logs_forward(tmp_path, vendor):
    evaluator = make_evaluator(tmp_path, vendor)
    iter_dir, agent_dir = tmp_path / "iter", tmp_path / "agent"
    point_dir = iter_dir / "points" / "point__0"
    point_dir.mkdir(parents=True)
    (point_dir / "lightningsim.log").write_text("log")
    agent_dir.mkdir()
    evaluator._collect_artifacts(
        iter_dir, agent_dir, [{"point_index": 0, "render_success": True}]
    )
    copied = agent_dir / "previous_design_artifacts" / "point__0" / "lightningsim.log"
    assert copied.read_text() == "log"


# ---- Constructor guards ------------------------------------------------------


def test_tools_mode_requires_a_vitis_mount(tmp_path, vendor):
    with pytest.raises(ValueError, match="requires vitis_dir"):
        make_evaluator(tmp_path, vendor, agent_dataflow_tools=True)
    make_evaluator(tmp_path, vendor, agent_dataflow_tools=True, vitis_dir=vendor)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"vitis_dir": "vendor"},
        {"vivado_dir": "vendor"},
        {"vitis_license_server": "2100@license"},
    ],
)
def test_tools_off_withholds_vitis_from_the_agent(tmp_path, vendor, kwargs):
    kwargs = {k: vendor if v == "vendor" else v for k, v in kwargs.items()}
    with pytest.raises(ValueError, match="withholds Vitis HLS"):
        make_evaluator(tmp_path, vendor, agent_dataflow_tools=False, **kwargs)


def test_release_mismatch_is_rejected(tmp_path, vendor):
    other = tmp_path / "vendor" / "2023.1"
    (other / "include").mkdir(parents=True)
    with pytest.raises(ValueError, match="releases differ"):
        make_evaluator(tmp_path, vendor, lightningsim_xilinx_hls=other)
    with pytest.raises(ValueError, match="releases differ"):
        make_evaluator(tmp_path, vendor, agent_dataflow_tools=True, vitis_dir=other)


def test_xilinx_hls_defaults_to_the_synthesis_tool(tmp_path, vendor):
    evaluator = make_evaluator(tmp_path, vendor)
    assert evaluator.lightningsim_xilinx_hls == vendor
    assert evaluator.lightningsim_tool.xilinx_hls == vendor


def test_bad_installation_and_timeout_are_rejected(tmp_path, vendor):
    with pytest.raises(ValueError, match="no include directory"):
        make_evaluator(tmp_path, vendor, lightningsim_xilinx_hls=tmp_path)
    with pytest.raises(ValueError, match="lightningsim_timeout"):
        make_evaluator(tmp_path, vendor, lightningsim_timeout=0)


# ---- The two agent-access modes ----------------------------------------------


@pytest.mark.parametrize("tools", [False, True])
def test_prompt_and_agent_environment_follow_the_mode(tmp_path, vendor, tools):
    evaluator = make_evaluator(
        tmp_path,
        vendor,
        agent_dataflow_tools=tools,
        vitis_dir=vendor if tools else None,
    )
    prompt = " ".join(
        evaluator._build_iteration_prompt(
            tmp_path, ["kernel.cpp"], "kernel_tb.cpp", "kernel", None
        ).split()
    )
    # Both modes are scored with LightningSim after synthesis.
    assert "the harness runs LightningSim on the synthesized point" in prompt
    # The Vitis report's latency is not what dataflow designs are scored on.
    assert "real latency" not in prompt
    assert "can be inaccurate for dataflow designs" in prompt
    assert ("installed and on PATH" in prompt) is tools
    assert ("NOT available in this environment" in prompt) is not tools
    # Without the tools the agent has no Vitis HLS either; with them it has it.
    assert ("Vitis HLS is NOT available" in prompt) is not tools
    assert ("Vitis HLS (`vitis_hls`) is on PATH" in prompt) is tools
    options = evaluator._agent_container_options()
    if tools:
        assert options == {"command_wrappers": ("with-dataflow-tools",)}
    else:
        assert options["tmpfs"] == {
            module.DATAFLOW_TOOLS_CONTAINER_DIR: "size=1m,mode=0755"
        }
        assert set(options["extra_hosts"]) == set(module.BLOCKED_HOSTS)


def test_refinement_prompt_reports_lightningsim_results(tmp_path, vendor):
    evaluator = make_evaluator(tmp_path, vendor)
    previous = {
        "agent_submitted": True,
        "can_parse_output": True,
        "points": [
            {
                "point_index": 0,
                "parameters": {"depth": 2},
                "render_success": True,
                "interface_preserved": True,
                "testbench_passed": True,
                "synthesis_passed": True,
                "lightningsim_passed": False,
                "lightningsim_status": "deadlock",
                "lightningsim_out": {
                    "data_execution": {"return_code": 1, "timeout": False},
                    "data_tool": {"deadlock": True},
                },
            }
        ],
    }
    prompt = evaluator._build_iteration_prompt(
        tmp_path, ["kernel.cpp"], "kernel_tb.cpp", "kernel", previous
    )
    assert "lightningsim FAILED (deadlock detected" in prompt
    assert "lightningsim.log" in prompt


@pytest.mark.parametrize("tools", [False, True])
def test_container_is_configured_by_mode(tmp_path, monkeypatch, vendor, tools):
    container = Mock()
    container.exec_run.return_value = (0, b"done")
    client = Mock()
    client.containers.run.return_value = container
    monkeypatch.setattr(
        "hls_eval.eval_agent_pi.eval_agent_pi.docker.from_env", lambda: client
    )
    monkeypatch.setattr(
        "hls_eval.eval_agent_pi.eval_agent_pi.VitisInstallation.from_path",
        lambda *args, **kwargs: SimpleNamespace(
            volumes={str(vendor): {"bind": "/opt/amd/hls", "mode": "ro"}},
            environment={"XILINX_HLS": "/opt/amd/hls"},
            hls_command=(),
        ),
    )
    evaluator = make_evaluator(
        tmp_path,
        vendor,
        agent_dataflow_tools=tools,
        vitis_dir=vendor if tools else None,
    )
    model = Mock()
    model.llm.model_name, model.llm.key = "test-model", "test-key"
    pools = EvalThreadPools(1, 1, 1, 1)
    try:
        evaluator._run_agent(tmp_path / "run", "prompt", model, pools)
    finally:
        pools.shutdown()
    options = client.containers.run.call_args.kwargs
    command = container.exec_run.call_args_list[0].args[0][-1]
    if tools:
        assert "with-vitis with-dataflow-tools pi -p" in command
        assert not options["tmpfs"] and not options["extra_hosts"]
    else:
        # No Vitis mount, environment or PATH wrapper for the agent.
        assert list(options["volumes"]) == [str(tmp_path / "run")]
        assert "XILINX_HLS" not in options["environment"]
        assert "with-vitis" not in command and "with-dataflow-tools" not in command
        assert options["tmpfs"] == {
            module.DATAFLOW_TOOLS_CONTAINER_DIR: "size=1m,mode=0755"
        }
        assert options["extra_hosts"]["sharc-lab.github.io"] == "127.0.0.1"


def test_run_pi_agent_default_container_options_are_unchanged(tmp_path, monkeypatch):
    container = Mock()
    container.exec_run.return_value = (0, b"done")
    client = Mock()
    client.containers.run.return_value = container
    monkeypatch.setattr(
        "hls_eval.eval_agent_pi.eval_agent_pi.docker.from_env", lambda: client
    )
    run_pi_agent(tmp_path / "run", "prompt", "test-model", "test-key")
    options = client.containers.run.call_args.kwargs
    assert not options["tmpfs"] and not options["extra_hosts"]
    assert container.exec_run.call_args_list[0].args[0][-1].endswith("pi -p prompt")


# ---- LightningSim output parsing and the CLI wrapper -------------------------


def test_parse_lightningsim_output():
    parsed = parse_lightningsim_output(LS_OUTPUT)
    assert parsed["latency_lightningsim_cycles"] == 1597077
    assert parsed["top_module"] == "forward" and not parsed["deadlock"]
    assert parse_lightningsim_output("[ERROR] Deadlock detected!\n")["deadlock"]
    assert "parse_error" in parse_lightningsim_output("nothing useful")


def fake_lightningsim(tmp_path, body):
    script = tmp_path / "fake_ls.py"
    script.write_text(body)
    script.chmod(script.stat().st_mode | stat.S_IEXEC)
    return LightningSimTool(tmp_path, command=(sys.executable, str(script)))


@pytest.mark.parametrize(
    ("body", "code", "timeout", "tool_data"),
    [
        (f"print({LS_OUTPUT!r})", 0, False, {"latency_lightningsim_cycles": 1597077}),
        (
            "import sys; print('Deadlock detected!'); sys.exit(1)",
            1,
            False,
            {"deadlock": True, "latency_lightningsim_cycles": None},
        ),
        ("import sys; sys.exit(2)", 2, False, None),
        ("import time; time.sleep(60)", -1, True, None),
    ],
)
def test_lightningsim_tool_outcomes(tmp_path, body, code, timeout, tool_data):
    tool = fake_lightningsim(tmp_path, body)
    tool.poll_interval = 0.05
    solution = tmp_path / "proj" / "solution1"
    solution.mkdir(parents=True)
    result = tool.run(solution, timeout=3)
    assert result.data_execution.return_code == code
    assert result.data_execution.timeout is timeout
    if tool_data is None:
        assert result.data_tool is None
    else:
        assert tool_data.items() <= result.data_tool.items()
        assert result.data_tool["peak_rss_mb"] >= 0
    assert (tmp_path / "proj" / "lightningsim.log").is_file()


def test_lightningsim_tool_passes_xilinx_hls(tmp_path):
    tool = fake_lightningsim(
        tmp_path,
        "import os; print('[0-7] top' if os.environ['XILINX_HLS'] else '')",
    )
    solution = tmp_path / "proj" / "solution1"
    solution.mkdir(parents=True)
    result = tool.run(solution, timeout=30)
    assert result.data_tool["latency_lightningsim_cycles"] == 7


def test_default_point_limit_is_eight_and_stated_in_the_prompt(tmp_path, vendor):
    evaluator = make_evaluator(tmp_path, vendor)
    assert evaluator.max_design_points == 8
    prompt = " ".join(
        evaluator._build_iteration_prompt(
            tmp_path, ["kernel.cpp"], "kernel_tb.cpp", "kernel", None
        ).split()
    )
    assert "Submit at most 8 design points" in prompt
    assert "a submission with more than 8 points is rejected as a whole" in prompt


def test_prompt_limit_follows_the_enforced_limit(tmp_path, vendor, design):  # noqa: F811
    evaluator = make_evaluator(tmp_path, vendor, max_design_points=3)
    prompt = " ".join(
        evaluator._build_iteration_prompt(
            tmp_path, ["kernel.cpp"], "kernel_tb.cpp", "kernel", None
        ).split()
    )
    assert "Submit at most 3 design points" in prompt
    agent = submission(design, tmp_path)
    (agent / "design_space.jsonl").write_text(
        "".join(f'{{"depth": {i}}}\n' for i in range(4))
    )
    checks, _, _ = evaluator._read_submission(
        design, agent, ["helper.cpp", "kernel.cpp"], "kernel_tb.cpp"
    )
    assert not checks["can_parse_output"]
    assert "Expected 2..3 design-space points, got 4" in checks["submission_error"]


def test_prompt_config_matches_what_the_synthesis_tool_writes(tmp_path):
    """The settings given to the agent must be the ones the harness synthesizes with."""
    vitis = tmp_path / "vitis"
    (vitis / "bin").mkdir(parents=True)
    launcher = vitis / "bin" / "vitis_hls"
    launcher.write_text("#!/bin/sh\nexit 1\n")  # the Tcl is written before launch
    launcher.chmod(0o755)
    source = tmp_path / "kernel.cpp"
    source.write_text("int kernel() { return 0; }\n")
    VitisHLSSynthTool(vitis).run(
        tmp_path / "build",
        [source],
        build_name="variant",
        hls_top_function="kernel",
        hls_unsafe_math=True,
        hls_disable_auto_optimizations=True,
    )
    tcl = (tmp_path / "build/vitis_hls_synth_tool__variant/run_hls.tcl").read_text()
    written = tuple(line for line in tcl.splitlines() if line.startswith("config_"))
    assert written == module.HARNESS_SYNTH_CONFIG_TCL


@requires_clang
def test_evaluator_synthesizes_with_the_settings_given_to_the_agent(
    evaluator,
    design,  # noqa: F811
    tmp_path,
    pools,
):
    evaluate(evaluator, design, submission(design, tmp_path), tmp_path, pools)
    for call in evaluator.vitis_hls_tool.run.call_args_list:
        assert call.kwargs["hls_unsafe_math"] is True
        assert call.kwargs["hls_disable_auto_optimizations"] is True


def flat_prompt(tmp_path, vendor, tools, **kwargs):
    evaluator = make_evaluator(
        tmp_path,
        vendor,
        agent_dataflow_tools=tools,
        vitis_dir=vendor if tools else None,
        **kwargs,
    )
    return " ".join(
        evaluator._build_iteration_prompt(
            tmp_path, ["kernel.cpp"], "kernel_tb.cpp", "kernel", None
        ).split()
    )


def test_tools_prompt_gives_the_harness_config_and_asks_for_timeouts(tmp_path, vendor):
    prompt = flat_prompt(
        tmp_path, vendor, True, synth_timeout=480, lightningsim_timeout=600
    )
    for line in module.HARNESS_SYNTH_CONFIG_TCL:
        assert line in prompt
    assert "exactly the settings the harness synthesizes every point with" in prompt
    assert (
        "Always give every `vitis_hls`, `lightningsim` and `fifo-advisor` command a timeout"
        in prompt
    )
    assert "timeout 480 vitis_hls -f run.tcl" in prompt
    assert "timeout 600 lightningsim proj/solution1" in prompt
    # Not claimed to be enforced on the agent's own runs.
    assert "each synthesis you run is also subject to" not in prompt


def test_tools_prompt_limits_vitis_to_producing_the_solution(tmp_path, vendor):
    prompt = flat_prompt(tmp_path, vendor, True)
    assert "use it for one thing only: producing the synthesized solution" in prompt
    assert "no csim_design or cosim" in prompt
    assert "Evaluate designs with LightningSim and FIFOAdvisor" in prompt
    assert "run real csynth_design yourself" not in prompt


def test_tools_prompt_says_not_to_overuse_vitis_and_that_feedback_comes_later(
    tmp_path, vendor
):
    prompt = flat_prompt(tmp_path, vendor, True)
    assert "Do not call Vitis HLS excessively" in prompt
    assert "at the start of your next iteration (if there is one)" in prompt
    assert "Vitis HLS feedback for each point" in prompt
    assert "synthesis logs" in prompt


def test_tools_off_prompt_has_no_tool_instructions(tmp_path, vendor):
    prompt = flat_prompt(tmp_path, vendor, False)
    assert "config_compile" not in prompt
    assert "Always give every" not in prompt
    assert "Do not call Vitis HLS excessively" not in prompt
    assert "vitis_hls -f run.tcl" not in prompt
