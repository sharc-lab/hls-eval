import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools
from hls_eval.eval_decomp.eval_decomp import (
    HLSDecompilationZeroShotEvaluator,
    _deidentify_rtl,
)
from hls_eval.llms import TAIPromptTooLong, TAITimeout
from hls_eval.tools import ExecutionData, ToolDataOutput, VitisHLSCSimTool


def tool_output(return_code=0, timeout=False):
    return ToolDataOutput(
        ExecutionData(return_code, "tool stdout", "", 1.0, 2.0, 1.0, timeout),
        None,
    )


@pytest.fixture
def setup_eval(tmp_path):
    design = tmp_path / "reference"
    design.mkdir()
    for name, content in {
        "top.txt": "top",
        "kernel_description.md": "SECRET_DESCRIPTION",
        "hls_eval_config.toml": 'tags = ["test"]\ntb_data = ["input.dat"]',
        "top.h": "int top(int a); // SECRET_HEADER",
        "top.cpp": "int top(int a) { return a + 1; } // SECRET_IMPLEMENTATION",
        "top_tb.cpp": '#include "top.h"\nint main() { return top(1) != 2; } // SECRET_TB',
        "input.dat": "SECRET_TEST_DATA",
    }.items():
        (design / name).write_text(content)

    def synthesize(build_dir, source_files, **kwargs):
        if build_dir.name == "ground_truth_build":
            rtl = build_dir / "project/solution__synth/syn/verilog"
            rtl.mkdir(parents=True)
            (rtl / "top.v").write_text("module top; endmodule")
            (rtl / "helper.sv").write_text("module helper; endmodule")
            (rtl / "rom.dat").write_text("0101")
            (rtl / "types.vh").write_text("`define WIDTH 32")
        return tool_output()

    synth = Mock()
    synth.run.side_effect = synthesize
    csim = Mock()
    csim.run.return_value = (tool_output(), tool_output())
    response = Mock(response_json={"id": "test-response"})
    response.text.return_value = (
        '<OUTPUT_CODE name="decompiled.cpp">'
        "int kernel_KERNEL_NAME(int a) { return a + 1; }"
        "</OUTPUT_CODE>"
    )
    model = SimpleNamespace(name="test-model", llm=Mock())
    model.llm.prompt.return_value = response
    evaluator = HLSDecompilationZeroShotEvaluator(
        csim,
        synth,
        tmp_path / "results",
        n_samples=2,
        hls_clock_period_ns=7.0,
        hls_compiler_defines=["SIZE=4"],
    )
    pools = EvalThreadPools(1, 1, 1, 1)
    state = SimpleNamespace(
        evaluator=evaluator,
        benchmark=BenchmarkCase(design),
        model=model,
        synth=synth,
        csim=csim,
        pools=pools,
        response=response,
        result_dir=tmp_path / "results/reference__test_model",
    )
    yield state
    pools.shutdown()


def evaluate(state):
    state.evaluator.evaluate_design(state.benchmark, state.model, state.pools)
    return json.loads((state.result_dir / "all_eval_data.json").read_text())


def test_decompilation_uses_rtl_and_validates_each_sample(setup_eval):
    state = setup_eval
    results = evaluate(state)
    assert len(results) == 2
    assert state.model.llm.prompt.call_count == 2
    assert state.synth.run.call_count == 3  # One golden synthesis for all samples.
    assert state.csim.run.call_count == 2
    golden_sources = state.synth.run.call_args_list[0].args[1]
    assert state.benchmark.tb_file not in golden_sources
    assert state.benchmark.kernel_fp in golden_sources

    for sample, data in results.items():
        assert data["pass_all"] is True
        assert data["pass_compile"] and data["pass_run"] and data["pass_synth"]
        assert "SECRET_" not in data["prompt"]
        for rtl_text in (
            "module kernel_KERNEL_NAME",
            "module helper",
            "0101",
            "`define WIDTH 32",
        ):
            assert rtl_text in data["prompt"]
        sample_dir = state.result_dir / f"sample__{sample}"
        assert json.loads((sample_dir / "single_eval_data.json").read_text()) == data
        assert (sample_dir / "raw_llm_prompt.txt").read_text() == data["prompt"]
        assert (sample_dir / "raw_llm_output.txt").read_text() == data["raw_output"]
        assert "kernel_KERNEL_NAME" in data["raw_output"]
        assert (
            data["generated_code"]["decompiled.cpp"]
            == "int top(int a) { return a + 1; }"
        )
        assert (sample_dir / "design_generated/decompiled.cpp").read_text() == data[
            "generated_code"
        ]["decompiled.cpp"]

    assert (state.result_dir / "rtl_synth/top.v").read_text() == "module top; endmodule"
    assert (
        state.result_dir / "rtl_synth_deidentified/kernel_KERNEL_NAME.v"
    ).read_text() == "module kernel_KERNEL_NAME; endmodule"

    for call in state.csim.run.call_args_list:
        sources = call.args[1]
        assert {p.name for p in sources} == {"decompiled.cpp", "top.h", "top_tb.cpp"}
        assert all("SECRET_IMPLEMENTATION" not in p.read_text() for p in sources)
        assert call.kwargs["aux_files"][0].read_text() == "SECRET_TEST_DATA"
        assert call.kwargs["hls_compiler_defines"] == ["SIZE=4"]
        assert call.kwargs["hls_clock_period_ns"] == 7.0
    for call in state.synth.run.call_args_list[1:]:
        assert [p.name for p in call.args[1]] == ["decompiled.cpp"]
        assert call.kwargs["hls_compiler_defines"] == ["SIZE=4"]
        assert call.kwargs["hls_disable_auto_optimizations"] is True
    assert "temperature" not in state.model.llm.prompt.call_args.kwargs


@pytest.mark.parametrize("kernel", ["kernel_2mm", "kernel_jacobi_2d"])
def test_kernel_identity_is_removed_from_entire_prompt(setup_eval, kernel):
    state = setup_eval
    state.benchmark.top_file.write_text(kernel)
    original_synth = state.synth.run.side_effect

    def synthesize(build_dir, *args, **kwargs):
        result = original_synth(build_dir, *args, **kwargs)
        if build_dir.name == "ground_truth_build":
            rtl = build_dir / "project/solution__synth/syn/verilog"
            (rtl / f"{kernel}.v").write_text(
                f'(* CORE_GENERATION_INFO="{kernel}_{kernel},hls_ip" *)\n'
                f"module {kernel};\n{kernel}_mul helper();\nendmodule // {kernel}"
            )
        return result

    state.synth.run.side_effect = synthesize
    results = evaluate(state)
    for data in results.values():
        assert kernel not in data["prompt"]
        assert kernel.removeprefix("kernel_") not in data["prompt"]
        assert "`kernel_KERNEL_NAME`" in data["prompt"]
        assert 'name="kernel_KERNEL_NAME.v"' in data["prompt"]
        assert "kernel_KERNEL_NAME_kernel_KERNEL_NAME,hls_ip" in data["prompt"]
        assert "kernel_KERNEL_NAME_mul helper();" in data["prompt"]
        assert f"int {kernel}(int a)" in data["generated_code"]["decompiled.cpp"]
    assert all(
        call.kwargs["hls_top_function"] == kernel
        for call in state.synth.run.call_args_list
    )
    assert all(
        call.kwargs["hls_top_function"] == kernel
        for call in state.csim.run.call_args_list
    )


def test_deidentification_preserves_helper_references_and_memory_data():
    rtl_files = {
        "kernel_2mm_kernel_2mm_helper.sv": 'module kernel_2mm_kernel_2mm_helper; $readmemh("rom/kernel_2mm.dat", mem); endmodule',
        "rom/kernel_2mm.dat": "0101\n1110\n",
    }
    result = _deidentify_rtl(rtl_files, "kernel_2mm")
    assert "kernel_KERNEL_NAME_kernel_KERNEL_NAME_helper.sv" in result
    assert (
        '"rom/kernel_KERNEL_NAME.dat"'
        in result["kernel_KERNEL_NAME_kernel_KERNEL_NAME_helper.sv"]
    )
    assert result["rom/kernel_KERNEL_NAME.dat"] == "0101\n1110\n"
    assert "rom/kernel_2mm.dat" in rtl_files


@pytest.mark.parametrize(
    "error,flag", [(TAITimeout, "model_timeout"), (TAIPromptTooLong, "prompt_too_long")]
)
def test_model_failures_are_saved_for_all_samples(setup_eval, error, flag):
    state = setup_eval
    state.model.llm.prompt.side_effect = error()
    results = evaluate(state)
    assert all(data[flag] and not data["pass_all"] for data in results.values())
    state.csim.run.assert_not_called()
    assert state.synth.run.call_count == 1


@pytest.mark.parametrize(
    "output",
    [
        "no code",
        '<OUTPUT_CODE name="decompiled.cpp"> </OUTPUT_CODE>',
        '<OUTPUT_CODE name="../top_tb.cpp">int main() { return 0; }</OUTPUT_CODE>',
    ],
)
def test_invalid_output_does_not_run_tools(setup_eval, output):
    state = setup_eval
    state.response.text.return_value = output
    results = evaluate(state)
    assert all(not data["can_parse_output"] for data in results.values())
    state.csim.run.assert_not_called()
    assert state.synth.run.call_count == 1


@pytest.mark.parametrize(
    "compile_result,run_result,synth_result",
    [
        (tool_output(1), None, tool_output()),
        (tool_output(), tool_output(1), tool_output()),
        (tool_output(), tool_output(0, timeout=True), tool_output()),
        (tool_output(), tool_output(), tool_output(1)),
    ],
)
def test_failed_validation_is_not_a_pass(
    setup_eval, compile_result, run_result, synth_result
):
    state = setup_eval
    golden_synth = state.synth.run.side_effect
    state.synth.run.side_effect = lambda build_dir, *args, **kwargs: (
        golden_synth(build_dir, *args, **kwargs)
        if build_dir.name == "ground_truth_build"
        else synth_result
    )
    state.csim.run.return_value = compile_result, run_result
    assert all(not data["pass_all"] for data in evaluate(state).values())


@pytest.mark.parametrize("missing_rtl", [False, True])
def test_invalid_golden_synthesis_stops_before_model(setup_eval, missing_rtl):
    state = setup_eval
    state.synth.run.side_effect = None
    state.synth.run.return_value = tool_output(0 if missing_rtl else 1)
    with pytest.raises(RuntimeError):
        evaluate(state)
    state.model.llm.prompt.assert_not_called()


def test_csim_passes_compiler_defines_to_vitis(tmp_path, monkeypatch):
    source = tmp_path / "candidate.cpp"
    source.write_text("int main() { return 0; }")
    process = Mock(returncode=1)
    process.communicate.return_value = ("", "stop after setup")
    monkeypatch.setattr("hls_eval.tools.subprocess.Popen", Mock(return_value=process))
    VitisHLSCSimTool(Path("/unused/vitis")).run(
        tmp_path / "build",
        [source],
        build_name="test",
        hls_compiler_defines=["SIZE=4", "-DFLAG"],
        warn_all=True,
    )
    tcl = next((tmp_path / "build").rglob("run_hls.tcl")).read_text()
    assert "-cflags {-DSIZE=4 -DFLAG -Wall -Wextra -Wno-unused-function}" in tcl
