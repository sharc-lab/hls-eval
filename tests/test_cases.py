import logging
from pathlib import Path

import pytest

from hls_eval.data import BenchmarkCase
from hls_eval.tools import CPPCompilerTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import unwrap

DIR_CURRENT = Path(__file__).resolve().parent
DIR_TEST = DIR_CURRENT
DIR_ROOT = DIR_CURRENT.parent
DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

LOGGER = logging.getLogger(__name__)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)


def find_benchmark_case_dirs(start_dir) -> list[Path]:
    all_dirs = [d for d in start_dir.rglob("*") if d.is_dir()]
    benchmark_case_dirs = [d for d in all_dirs if (d / "hls_eval_config.toml").exists()]
    return benchmark_case_dirs


ALL_BENCHMARK_CASES = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_cases_load(case_dir):
    benchmark_case = BenchmarkCase(case_dir)
    assert benchmark_case


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_cases_compile_and_run(case_dir, tmp_path):
    benchmark_case = BenchmarkCase(case_dir)
    benchmark_case_synth = benchmark_case.copy_to(tmp_path)

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool_compiler = CPPCompilerTool(vitis_hls_dir)

    results_compile, results_run = tool_compiler.run(
        tmp_path,
        source_files=benchmark_case_synth.source_files,
        build_name=benchmark_case_synth.name,
    )

    assert results_compile.data_execution.return_code == 0
    assert results_compile.data_execution.timeout is False
    assert results_compile.data_execution.execution_time > 0

    assert results_run is not None
    assert results_run.data_execution.return_code == 0
    assert results_run.data_execution.timeout is False
    assert results_run.data_execution.execution_time > 0


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_cases_synth(case_dir, tmp_path):
    benchmark_case = BenchmarkCase(case_dir)
    benchmark_case_synth = benchmark_case.copy_to(tmp_path)

    LOGGER.debug(f"Running HLS synthesis case_dir {case_dir}")
    LOGGER.debug(f"Running HLS synthesis in {tmp_path}")

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool_hls = VitisHLSSynthTool(vitis_hls_dir)

    results = tool_hls.run(
        tmp_path,
        source_files=benchmark_case_synth.source_files,
        build_name=benchmark_case_synth.name,
        hls_top_function=benchmark_case_synth.top_fn,
    )

    assert results.data_execution.return_code == 0
    assert results.data_execution.timeout is False
    assert results.data_execution.execution_time > 0
