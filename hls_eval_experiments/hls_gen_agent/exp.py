import logging
from pathlib import Path

from dotenv import dotenv_values

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.eval_agent import HLSGenerationAgentEvaluator
from hls_eval.llms import build_model_remote_openrouter
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import check_key, unwrap

EXP_NAME = "hls_gen_agent"

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent

DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

DIR_CURRENT_OUTPUT_DATA = DIR_CURRENT / "output_data"
if not DIR_CURRENT_OUTPUT_DATA.exists():
    DIR_CURRENT_OUTPUT_DATA.mkdir()

LOGGER = logging.getLogger(EXP_NAME)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)

API_KEY_OPENROUTER = check_key(dotenv_values(".env")["OPENROUTER_API_KEY"])


if __name__ == "__main__":
    all_benchmark_case_dirs = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)
    all_benchmark_cases = [
        BenchmarkCase(d, name=d.name) for d in all_benchmark_case_dirs
    ]

    sets_to_test = set(["polybench"])

    all_benchmark_cases = [
        bc
        for bc in all_benchmark_cases
        if len(set(bc.tags_all).intersection(sets_to_test)) > 0
    ]
    
    all_benchmark_cases = sorted(all_benchmark_cases, key=lambda x: x.name)
    

    model_names_to_test = ["openai/gpt-oss-120b"]
    models = [
        build_model_remote_openrouter(model_name, api_key=API_KEY_OPENROUTER)
        for model_name in model_names_to_test
    ]
    models_map = {
        model_name: model for model_name, model in zip(model_names_to_test, models)
    }

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")


    evaluator = HLSGenerationAgentEvaluator(
        vitis_hls_tool_csim=VitisHLSCSimTool(vitis_hls_dir),
        vitis_hls_tool_synth=VitisHLSSynthTool(vitis_hls_dir),
        output_data_dir=DIR_CURRENT_OUTPUT_DATA,
        n_samples=5,
    )

    benchmark_cases_filtered = all_benchmark_cases[:1]
    models_filtered = models[:1]

    evaluator.evaluate_designs(
        benchmark_cases=benchmark_cases_filtered,
        models=models_filtered,
        n_jobs=64,
        n_jobs_pool_llm=64,
        n_jobs_pool_agent=64,
        n_jobs_pool_csim=64,
        n_jobs_pool_synth=64,
    )

