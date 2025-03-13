import logging
from pathlib import Path

import pytest

from hls_eval.data import BenchmarkCase, find_benchmark_case_dirs
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool, auto_find_vitis_hls_dir
from hls_eval.utils import unwrap

DIR_CURRENT = Path(__file__).resolve().parent
DIR_TEST = DIR_CURRENT
DIR_ROOT = DIR_CURRENT.parent
DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

LOGGER = logging.getLogger(__name__)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)


ALL_BENCHMARK_CASES = find_benchmark_case_dirs(DIR_HLS_EVAL_DATA)

tag_to_keep = "c2hlsc"
if tag_to_keep:
    ALL_BENCHMARK_CASES = [
        d for d in ALL_BENCHMARK_CASES if tag_to_keep in BenchmarkCase(d).tags_all
    ]
else:
    ALL_BENCHMARK_CASES = list(ALL_BENCHMARK_CASES)


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_cases_load__all(case_dir):
    benchmark_case = BenchmarkCase(case_dir, name=case_dir.name)
    assert benchmark_case


@pytest.mark.parametrize(
    "case_dir", ALL_BENCHMARK_CASES, ids=[d.name for d in ALL_BENCHMARK_CASES]
)
def test_cases_compile_and_run__all(case_dir, tmp_path: Path):
    LOGGER.debug(f"Running compile and run in tmp_path: {tmp_path}")

    benchmark_case = BenchmarkCase(case_dir, name=case_dir.name)
    benchmark_case_synth = benchmark_case.copy_to(tmp_path / "design_base")

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool_compiler = VitisHLSCSimTool(vitis_hls_dir)

    results_compile, results_run = tool_compiler.run(
        tmp_path,
        source_files=benchmark_case_synth.source_files,
        aux_files=benchmark_case_synth.not_source_files,
        build_name=benchmark_case_synth.name,
        warn_all=False,
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
def test_cases_synth__all(case_dir, tmp_path):
    LOGGER.debug(f"Running HLS synthesis in case_dir {tmp_path}")

    benchmark_case = BenchmarkCase(case_dir, name=case_dir.name)
    benchmark_case_synth = benchmark_case.copy_to(tmp_path / "design_base")

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
