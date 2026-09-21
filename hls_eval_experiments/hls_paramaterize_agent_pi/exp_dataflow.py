import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import dotenv_values

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.eval_agent_pi.eval_agent_pi_paramaterized_dataflow import (
    HLSParameterizationIterativeDataflowAgentEvaluatorPi,
)
from hls_eval.llms import build_model_remote_openrouter
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import check_key, unwrap

EXP_NAME = "hls_paramaterize_dataflow_agent"

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent

DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data_accel"

# Two runs of the same dataflow evaluator, in parallel, each with its own output
# folder. What differs is the agent's environment while it works:
#   agent_vitis_and_tools:  Vitis HLS (vitis_hls) plus LightningSim and FIFOAdvisor
#   agent_no_vitis_no_tools: neither Vitis HLS nor the tools; only clang and the
#                            testbench to check its work
# In both runs the harness itself always runs csim, Vitis HLS synthesis and
# LightningSim on the host to score every iteration.
AGENT_HAS_VITIS_AND_TOOLS_BY_RUN: dict[str, bool] = {
    "agent_vitis_and_tools": True,
    "agent_no_vitis_no_tools": False,
}
DIR_OUTPUT_BY_RUN = {
    run: DIR_CURRENT / f"output_data_dataflow__{run}"
    for run in AGENT_HAS_VITIS_AND_TOOLS_BY_RUN
}
for dir_output in DIR_OUTPUT_BY_RUN.values():
    dir_output.mkdir(exist_ok=True)

# Each evaluator builds its own pools, so the two runs together use twice this
# many workers (agents, csim, synthesis and LightningSim runs at ~1.5 GB each).
N_JOBS_PER_RUN = 36

LOGGER = logging.getLogger(EXP_NAME)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)

API_KEY_OPENROUTER = check_key(dotenv_values(".env")["OPENROUTER_API_KEY"])

if __name__ == "__main__":
    all_benchmark_case_dirs = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)
    all_benchmark_cases = [
        BenchmarkCase(d, name=d.name) for d in all_benchmark_case_dirs
    ]

    # all designs tagged stream_hls in hls_eval_data_accel (whatever is present
    # in the working tree)
    sets_to_test: set[str] = {
        "stream_hls",
    }

    all_benchmark_cases = [
        bc
        for bc in all_benchmark_cases
        if len(set(bc.tags_all).intersection(sets_to_test)) > 0
    ]

    all_benchmark_cases = sorted(all_benchmark_cases, key=lambda x: x.name)
    if not all_benchmark_cases:
        raise RuntimeError(f"No benchmark cases tagged {sets_to_test} found")

    # all_benchmark_cases = all_benchmark_cases[:1]

    model_names_to_test = ["deepseek/deepseek-v4.1-flash"]
    models = [
        build_model_remote_openrouter(model_name, api_key=API_KEY_OPENROUTER)
        for model_name in model_names_to_test
    ]
    models_map = {
        model_name: model for model_name, model in zip(model_names_to_test, models)
    }

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")

    # The same Vitis HLS release is used for the harness's csim, synthesis and
    # LightningSim (its XILINX_HLS defaults to the synthesis tool's directory) and
    # the copy mounted in the vitis_and_tools agent container. Validated with 2024.1.
    #
    # The host also needs the LightningSim Pixi environment installed once:
    #   cd hls_eval/eval_agent_pi/docker/dataflow_tools && pixi install
    # and the agent image built once (after the base image):
    #   bash hls_eval/eval_agent_pi/docker/build_docker_image_dataflow.sh
    def build_evaluator(
        run: str,
    ) -> HLSParameterizationIterativeDataflowAgentEvaluatorPi:
        return HLSParameterizationIterativeDataflowAgentEvaluatorPi(
            vitis_hls_tool_csim=VitisHLSCSimTool(vitis_hls_dir),
            vitis_hls_tool_synth=VitisHLSSynthTool(vitis_hls_dir),
            output_data_dir=DIR_OUTPUT_BY_RUN[run],
            n_samples=1,
            n_iters=3,
            # Vitis is mounted for the agent only together with the tools (LightningSim
            # needs it); the no-Vitis run passes nothing, and the evaluator rejects
            # a Vitis mount when the tools are off.
            vitis_dir=vitis_hls_dir if AGENT_HAS_VITIS_AND_TOOLS_BY_RUN[run] else None,
            agent_dataflow_tools=AGENT_HAS_VITIS_AND_TOOLS_BY_RUN[run],
            lightningsim_timeout=60 * 10,
        )

    # Build both up front so a configuration error fails before any agent runs.
    evaluators = {run: build_evaluator(run) for run in AGENT_HAS_VITIS_AND_TOOLS_BY_RUN}
    for run, evaluator in evaluators.items():
        expected = AGENT_HAS_VITIS_AND_TOOLS_BY_RUN[run]
        assert evaluator.agent_dataflow_tools is expected, run
        assert (evaluator.vitis_dir is not None) is expected, run

    def run_evaluation(run: str) -> None:
        print(f"Run {run} started: {DIR_OUTPUT_BY_RUN[run]}", flush=True)
        # LightningSim runs on the evaluator's own pool, the same size as its
        # synthesis pool.
        evaluators[run].evaluate_designs(
            benchmark_cases=all_benchmark_cases,
            models=models,
            n_jobs=N_JOBS_PER_RUN,
            n_jobs_pool_llm=N_JOBS_PER_RUN,
            n_jobs_pool_agent=N_JOBS_PER_RUN,
            n_jobs_pool_csim=N_JOBS_PER_RUN,
            n_jobs_pool_synth=N_JOBS_PER_RUN,
        )

    # One failing run must not stop the other: wait for both, then report.
    errors: dict[str, BaseException] = {}
    with ThreadPoolExecutor(
        max_workers=len(evaluators), thread_name_prefix="dataflow-run"
    ) as executor:
        futures = {executor.submit(run_evaluation, run): run for run in evaluators}
        for future in as_completed(futures):
            run = futures[future]
            try:
                future.result()
                print(f"Run {run} finished: {DIR_OUTPUT_BY_RUN[run]}", flush=True)
            except Exception as error:
                LOGGER.exception("Run %s failed", run)
                errors[run] = error
    if errors:
        raise RuntimeError(
            "Failed runs: "
            + ", ".join(f"{run}: {error!r}" for run, error in errors.items())
        )
