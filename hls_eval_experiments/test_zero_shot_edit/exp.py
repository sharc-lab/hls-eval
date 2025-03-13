import logging
from pathlib import Path

from dotenv import dotenv_values

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.eval import HLSEditingZeroShotEvaluator, HLSGenerationZeroShotEvaluator
from hls_eval.llms import build_model_remote_tai
from hls_eval.prompts import prompt_loop_tiling
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import check_key, unwrap

EXP_NAME = "test_zero_shot_gen"

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent

DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

DIR_CURRENT_OUTPUT_DATA = DIR_CURRENT / "output_data"
if not DIR_CURRENT_OUTPUT_DATA.exists():
    DIR_CURRENT_OUTPUT_DATA.mkdir()

LOGGER = logging.getLogger(EXP_NAME)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)

API_KEY_TOGETHERAI = check_key(dotenv_values(".env")["TOGETHER_API_KEY"])


if __name__ == "__main__":
    all_benchmark_case_dirs = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)
    all_benchmark_cases = [
        BenchmarkCase(d, name=d.name) for d in all_benchmark_case_dirs
    ]

    sets_to_test = set(["polybench", "c2hlsc"])

    all_benchmark_cases = [
        bc
        for bc in all_benchmark_cases
        if len(set(bc.tags_all).intersection(sets_to_test)) > 0
    ]
    all_benchmark_cases_map = {bc.name: bc for bc in all_benchmark_cases}

    model_names_to_test = [
        "Qwen/Qwen2.5-Coder-32B-Instruct",
        "google/gemma-2-27b-it",
        "meta-llama/Llama-3-70b-chat-hf",
        "meta-llama/Llama-3-8b-chat-hf",
    ]
    models = [
        build_model_remote_tai(model_name, api_key=API_KEY_TOGETHERAI)
        for model_name in model_names_to_test
    ]
    models_map = {
        model_name: model for model_name, model in zip(model_names_to_test, models)
    }

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")

    prompt_task = prompt_loop_tiling

    evaluator = HLSEditingZeroShotEvaluator(
        vitis_hls_tool_csim=VitisHLSCSimTool(vitis_hls_dir),
        vitis_hls_tool_synth=VitisHLSSynthTool(vitis_hls_dir),
        output_data_dir=DIR_CURRENT_OUTPUT_DATA,
        prompt_task=prompt_task,
        n_samples=4,
        temperature=0.7,
    )

    # evaluator.evaluate_designs(
    #     benchmark_cases=all_benchmark_cases,
    #     models=models,
    #     n_jobs=16,
    #     n_jobs_pool_llm=4,
    #     n_jobs_pool_csim=8,
    #     n_jobs_pool_synth=12,
    # )

    # one off runs to get any by hand that failed for some network reasons
    # one_off_benchmark_cases = [bc for bc in all_benchmark_cases if bc.name == "fdtd-2d"]
    # one_off_models = [m for m in models if m.name == "google/gemma-2-27b-it"]

    one_off_cases = [
        ("gemm", "meta-llama/Llama-3-8b-chat-hf"),
        ("atax", "meta-llama/Llama-3-8b-chat-hf"),
    ]

    one_off_cases_objects = [
        (all_benchmark_cases_map[case_name], models_map[model_name])
        for case_name, model_name in one_off_cases
    ]

    evaluator.evaluate_design_model_pairs(
        one_off_cases_objects,
        n_jobs=16,
        n_jobs_pool_llm=4,
        n_jobs_pool_csim=16,
        n_jobs_pool_synth=16,
    )
