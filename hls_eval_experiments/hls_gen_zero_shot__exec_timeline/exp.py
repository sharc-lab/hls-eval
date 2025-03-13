import logging
from pathlib import Path

from dotenv import dotenv_values

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.eval import HLSGenerationZeroShotEvaluator
from hls_eval.llms import build_model_remote_tai
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import check_key, unwrap

EXP_NAME = "hls_gen_zero_shot__exec_timeline"

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent

DIR_HLS_EVAL_DESIGNS = DIR_ROOT / "hls_eval_data"

DIR_CURRENT_OUTPUT_DATA = DIR_CURRENT / "output_data"
if not DIR_CURRENT_OUTPUT_DATA.exists():
    DIR_CURRENT_OUTPUT_DATA.mkdir()

LOGGER = logging.getLogger(EXP_NAME)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)

API_KEY_TOGETHERAI = check_key(dotenv_values(".env")["TOGETHER_API_KEY"])


if __name__ == "__main__":
    all_benchmark_case_dirs = find_benchmark_case_dirs(DIR_HLS_EVAL_DESIGNS)
    all_benchmark_cases = [
        BenchmarkCase(d, name=d.name) for d in all_benchmark_case_dirs
    ]

    model_to_test = "Qwen/Qwen2.5-Coder-32B-Instruct"
    model = build_model_remote_tai(model_to_test, api_key=API_KEY_TOGETHERAI)

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")

    evaluator = HLSGenerationZeroShotEvaluator(
        vitis_hls_tool_csim=VitisHLSCSimTool(vitis_hls_dir),
        vitis_hls_tool_synth=VitisHLSSynthTool(vitis_hls_dir),
        output_data_dir=DIR_CURRENT_OUTPUT_DATA,
    )

    evaluator.evaluate_designs(
        all_benchmark_cases,
        [model],
        n_jobs=16,
        n_jobs_pool_llm=4,
        n_jobs_pool_csim=8,
        n_jobs_pool_synth=8,
    )
