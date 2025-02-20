import logging
from pathlib import Path

import pytest

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.prompts import build_prompt_gen_zero_shot

DIR_CURRENT = Path(__file__).resolve().parent
DIR_TEST = DIR_CURRENT
DIR_ROOT = DIR_CURRENT.parent
DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

LOGGER = logging.getLogger(__name__)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)


ALL_BENCHMARK_CASES = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_prompt_gen_zero_shot(case_dir):
    benchmark_case = BenchmarkCase(case_dir, name=case_dir.name)
    assert benchmark_case

    kernel_description_fp = benchmark_case.kernel_description_fp
    tb_file = benchmark_case.tb_file
    header_files = benchmark_case.h_files
    assert len(header_files) == 1
    header_file = header_files[0]

    prompt = build_prompt_gen_zero_shot(
        kernel_description_fp,
        tb_file,
        header_file,
    )
    assert prompt
    print()
    print(prompt)
