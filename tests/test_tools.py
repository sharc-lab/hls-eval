import logging
import shutil
from pathlib import Path

from hls_eval.tools import (
    VitisHLSCoSimTool,
    VitisHLSCSimTool,
    VitisHLSSynthTool,
    auto_find_vitis_hls_dir,
)
from hls_eval.utils import unwrap

DIR_CURRENT = Path(__file__).resolve().parent
DIR_TEST_DESIGN = DIR_CURRENT / "test_design_for_tools"

LOGGER = logging.getLogger(__name__)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)

SOURCE_FILE_NAMES = ["vec_add.cpp", "vec_add.h"]
TB_FILE_NAME = "vec_add_tb.cpp"
TOP_FN = "vec_add"


def _copy_design_to(dest: Path) -> tuple[list[Path], list[Path]]:
    dest.mkdir(parents=True, exist_ok=True)

    source_files = []
    for name in SOURCE_FILE_NAMES:
        src = DIR_TEST_DESIGN / name
        dst = dest / name
        shutil.copy(src, dst)
        source_files.append(dst)

    aux_files = []
    tb_src = DIR_TEST_DESIGN / TB_FILE_NAME
    tb_dst = dest / TB_FILE_NAME
    shutil.copy(tb_src, tb_dst)
    aux_files.append(tb_dst)

    return source_files, aux_files


def test_vitis_hls_synth_tool(tmp_path: Path):
    LOGGER.info(f"Running VitisHLSSynthTool in tmp_path: {tmp_path}")
    design_dir = tmp_path / "design_base"
    source_files, _ = _copy_design_to(design_dir)

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool = VitisHLSSynthTool(vitis_hls_dir)

    result = tool.run(
        tmp_path,
        source_files=source_files,
        build_name="vec_add",
        hls_top_function=TOP_FN,
    )

    assert result.data_execution.timeout is False
    assert result.data_execution.return_code == 0
    assert result.data_execution.execution_time > 0
    assert result.data_tool is not None


def test_vitis_hls_csim_tool(tmp_path: Path):
    LOGGER.info(f"Running VitisHLSCSimTool in tmp_path: {tmp_path}")
    design_dir = tmp_path / "design_base"
    source_files, aux_files = _copy_design_to(design_dir)

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool = VitisHLSCSimTool(vitis_hls_dir)

    results_compile, results_run = tool.run(
        tmp_path,
        source_files=source_files,
        aux_files=aux_files,
        build_name="vec_add",
        hls_top_function=TOP_FN,
    )

    assert results_compile.data_execution.timeout is False
    assert results_compile.data_execution.return_code == 0
    assert results_compile.data_execution.execution_time > 0

    assert results_run is not None
    assert results_run.data_execution.timeout is False
    assert results_run.data_execution.return_code == 0
    assert results_run.data_execution.execution_time > 0
    assert "Test passed!" in results_run.data_execution.stdout


def test_vitis_hls_cosim_tool(tmp_path: Path):
    LOGGER.info(f"Running VitisHLSCoSimTool in tmp_path: {tmp_path}")
    design_dir = tmp_path / "design_base"
    source_files, aux_files = _copy_design_to(design_dir)

    vitis_hls_dir = unwrap(auto_find_vitis_hls_dir(), "Vitis HLS bin not auto found")
    tool = VitisHLSCoSimTool(vitis_hls_dir)

    result = tool.run(
        tmp_path,
        source_files=source_files,
        aux_files=aux_files,
        build_name="vec_add",
        hls_top_function=TOP_FN,
    )

    assert result.data_execution.timeout is False
    assert result.data_execution.return_code == 0
    assert result.data_execution.execution_time > 0
    assert result.data_tool is not None
    assert "data_synthesis" in result.data_tool
    assert "data_cosim" in result.data_tool
