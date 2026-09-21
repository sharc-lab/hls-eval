"""Sanity checks of the real LightningSim/FIFOAdvisor install on `stream_hls/atax`.

These run Vitis HLS synthesis and the tools in the repo's Pixi environment
(`hls_eval/eval_agent_pi/docker/dataflow_tools`; `pixi install` there first), so
they are skipped when Vitis HLS or that environment is missing. No LLM is used.
The in-container equivalents are in `docker/test_dataflow_image.sh`.
"""

import json
import os
import shutil
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import pytest

from hls_eval.eval import EvalThreadPools
from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized_dataflow import (
    LATENCY_KEY,
    HLSParameterizationIterativeDataflowAgentEvaluatorPi,
)
from hls_eval.eval_agent_pi.lightningsim import (
    DATAFLOW_TOOLS_DIR,
    LightningSimTool,
    default_lightningsim_command,
)
from hls_eval.tools import (
    VitisHLSCSimTool,
    VitisHLSSynthTool,
    auto_find_vitis_hls_dir,
)

ROOT = Path(__file__).resolve().parent.parent
ATAX = ROOT / "hls_eval_data_accel" / "stream_hls" / "atax"
VITIS = auto_find_vitis_hls_dir()

pytestmark = pytest.mark.skipif(
    VITIS is None
    or shutil.which("pixi") is None
    or not (DATAFLOW_TOOLS_DIR / ".pixi").is_dir()
    or not ATAX.is_dir(),
    reason="needs Vitis HLS on PATH, pixi, and `pixi install` in docker/dataflow_tools",
)

SOURCES = ["atax.cpp"]
TB = "atax_tb.cpp"
TB_DATA = ["input_0.bin", "input_1.bin", "output_0.bin"]


def pixi_run(*args, cwd=None, check=True):
    command = [*default_lightningsim_command()[:-1], *args]
    env = {**os.environ, "XILINX_HLS": str(VITIS)}
    return subprocess.run(
        command, capture_output=True, text=True, cwd=cwd, env=env, check=check
    )


@pytest.fixture(scope="module")
def synthesized(tmp_path_factory):
    """atax synthesized by the real synth tool with its testbench registered."""
    design = tmp_path_factory.mktemp("atax") / "design"
    shutil.copytree(ATAX, design)
    build = design.parent / "build"
    tool = VitisHLSSynthTool(VITIS)
    result = tool.run(
        build,
        [design / name for name in SOURCES],
        build_name="variant",
        hls_top_function=ATAX.joinpath("top.txt").read_text().strip(),
        hls_disable_auto_optimizations=True,
        tb_files=[design / TB, *(design / name for name in TB_DATA)],
        timeout=600,
    )
    assert result.data_execution.return_code == 0, result.data_execution.stdout[-2000:]
    solution = (
        build
        / "vitis_hls_synth_tool__variant"
        / "vitis_hls_synth_tool__variant__proj"
        / "solution__synth"
    )
    return solution, result.data_tool


def test_tools_are_installed_in_the_pixi_environment():
    pixi_run("python", "-c", "import lightningsim, fifo_advisor")
    assert "solution_dir" in pixi_run("lightningsim", "--help").stdout
    assert "solution_dir" in pixi_run("fifo-advisor", "--help").stdout
    # Activation must give LightningSim conda's compilers, not the system's.
    cc = pixi_run("python", "-c", "import os; print(os.environ['CC'])").stdout
    assert "conda" in cc


def test_lightningsim_measures_atax_deterministically(synthesized):
    solution, synth_data = synthesized
    tool = LightningSimTool(VITIS)
    first = tool.run(solution, timeout=600)
    second = tool.run(solution, timeout=600)
    for run in (first, second):
        assert run.data_execution.return_code == 0
        assert run.data_tool["latency_lightningsim_cycles"] > 0
        assert not run.data_tool["deadlock"]
    assert (
        first.data_tool["latency_lightningsim_cycles"]
        == second.data_tool["latency_lightningsim_cycles"]
    )
    print(
        "atax latency: LightningSim",
        first.data_tool["latency_lightningsim_cycles"],
        "vs Vitis estimate",
        synth_data["latency_worst_cycles"],
    )


@pytest.mark.parametrize(
    "solver_args",
    [
        ("--baseline",),
        ("--solver", "heuristic"),
        ("--solver", "random", "--n-samples", "50", "--seed", "7"),
    ],
    ids=["baseline", "heuristic", "random"],
)
def test_fifo_advisor_on_atax(synthesized, tmp_path, solver_args):
    solution, _ = synthesized
    out = tmp_path / "result.json"
    pixi_run("fifo-advisor", str(solution), *solver_args, "--output", str(out))
    evaluations = json.loads(out.read_text())["evaluations"]
    ok = [e for e in evaluations if not e["deadlock"]]
    assert ok and all(
        e["latency"] > 0 and e["bram_usage_total"] is not None for e in ok
    )
    if solver_args == ("--baseline",):
        # The default-depth configuration is what LightningSim simulates.
        reference = LightningSimTool(VITIS).run(solution, timeout=600)
        assert (
            evaluations[0]["latency"]
            == reference.data_tool["latency_lightningsim_cycles"]
        )


def test_lightningsim_runs_in_parallel_on_a_pool(synthesized):
    solution, _ = synthesized
    tool = LightningSimTool(VITIS)
    with ThreadPoolExecutor(max_workers=4) as pool:
        runs = list(
            pool.map(
                lambda i: tool.run(solution, 600, solution.parent / f"p{i}.log"),
                range(4),
            )
        )
    latencies = {r.data_tool["latency_lightningsim_cycles"] for r in runs}
    assert len(latencies) == 1
    print("peak RSS MB per run:", [round(r.data_tool["peak_rss_mb"]) for r in runs])


def test_evaluator_synth_then_lightningsim_stage(tmp_path):
    """The evaluator's real per-point path, with real csim, csynth and LightningSim."""
    design = tmp_path / "design"
    shutil.copytree(ATAX, design)
    evaluator = HLSParameterizationIterativeDataflowAgentEvaluatorPi(
        VitisHLSCSimTool(VITIS),
        VitisHLSSynthTool(VITIS),
        tmp_path / "results",
        agent_dataflow_tools=False,
        csim_timeout=600,
        synth_timeout=600,
    )
    pools = EvalThreadPools(1, 1, 2, 2)
    try:
        result = evaluator._evaluate_variant(
            design, SOURCES, TB, ATAX.joinpath("top.txt").read_text().strip(), pools
        )
    finally:
        pools.shutdown()
        evaluator._shutdown_lightningsim_pools()
    assert result["lightningsim_status"] == "passed", result.get("lightningsim_out")
    assert result["passed"]
    metrics = result["vitis_hls_tool_out"]["data_tool"]
    assert metrics[LATENCY_KEY] == result[LATENCY_KEY] > 0
    assert (tmp_path / "lightningsim.log").is_file()
