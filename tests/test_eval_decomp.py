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


def _tool_output(stdout="", stderr="", return_code=0, data_tool=None):
    return ToolDataOutput(
        ExecutionData(return_code, stdout, stderr, 1.0, 2.0, 1.0, False), data_tool
    )


def _dump(*values):
    return (
        "==BEGIN DUMP_ARRAYS==\nbegin dump: D\n"
        + " ".join(values)
        + "\nend   dump: D\n==END   DUMP_ARRAYS==\n"
    )


def test_array_dump_extraction():
    from hls_eval.eval_decomp.eval_decomp import _extract_array_dump

    assert _extract_array_dump("no dump here") is None
    assert _extract_array_dump(_dump("1.0", "2.0")) == [
        "begin", "dump:", "D", "1.0", "2.0", "end", "dump:", "D",
    ]


def test_empty_design_detection():
    from hls_eval.eval_decomp.eval_decomp import _is_empty_design

    used = {"resources_lut_used": 10}
    assert _is_empty_design(_tool_output(data_tool={"resources_lut_used": 0}))
    assert _is_empty_design(
        _tool_output("WARNING: [SYNCHK 200-77] has no outputs", data_tool=used)
    )
    assert not _is_empty_design(_tool_output(data_tool=used))


def _run_with_tb_outputs(state, reference_stderr, candidate_stderr, synth_data):
    def run(build_dir, sources, aux_files=(), build_name=None, **kwargs):
        stderr = reference_stderr if "reference_tb" in build_name else candidate_stderr
        return _tool_output(), _tool_output(stderr=stderr)

    state.csim.run.side_effect = run
    original = state.synth.run.side_effect

    def synthesize(build_dir, *args, **kwargs):
        out = original(build_dir, *args, **kwargs)
        if build_dir.name != "ground_truth_build":
            return _tool_output(data_tool=synth_data)
        return _tool_output(data_tool={"resources_lut_used": 5})

    state.synth.run.side_effect = synthesize
    return evaluate(state)


def test_functional_pass_requires_matching_output_dump(setup_eval):
    used = {"resources_lut_used": 5}
    results = _run_with_tb_outputs(setup_eval, _dump("1.0"), _dump("1.0"), used)
    assert all(d["pass_functional"] for d in results.values())
    assert results[next(iter(results))]["functional_check"] == "output_dump"


def test_functional_fails_when_output_dump_differs(setup_eval):
    used = {"resources_lut_used": 5}
    results = _run_with_tb_outputs(setup_eval, _dump("1.0"), _dump("9.0"), used)
    assert not any(d["pass_functional"] for d in results.values())
    assert all(d["pass_compile_tb"] for d in results.values())


def test_functional_falls_back_to_exit_code_without_dump(setup_eval):
    used = {"resources_lut_used": 5}
    results = _run_with_tb_outputs(setup_eval, "", "", used)
    assert all(d["pass_functional"] for d in results.values())
    assert results[next(iter(results))]["functional_check"] == "return_code"


def test_empty_synthesis_does_not_pass_synth(setup_eval):
    results = _run_with_tb_outputs(
        setup_eval, "", "", {"resources_lut_used": 0}
    )
    for data in results.values():
        assert data["synth_return_code_zero"] is True
        assert data["synth_empty_design"] is True
        assert data["pass_synth"] is False


def test_testbench_is_built_with_signature_check_wrapper(setup_eval):
    state = setup_eval
    _run_with_tb_outputs(state, "", "", {"resources_lut_used": 5})
    candidate_calls = [
        c for c in state.csim.run.call_args_list if "reference_tb" not in c.args[3]
    ]
    assert candidate_calls
    for call in candidate_calls:
        assert "decompiled_signature_checked.cpp" in {p.name for p in call.args[1]}
        assert "decompiled.cpp" not in {p.name for p in call.args[1]}
        wrapper = next(
            p for p in call.args[1] if p.name == "decompiled_signature_checked.cpp"
        )
        text = wrapper.read_text()
        assert text.index('#include "top.h"') < text.index("decompiled_impl.inc")


def test_synthesis_reports_are_sanitized(tmp_path):
    from hls_eval.eval_decomp.eval_decomp import _collect_synthesis_reports

    proj = tmp_path / "proj/solution__synth"
    (proj / "syn/report").mkdir(parents=True)
    (proj / ".autopilot/db").mkdir(parents=True)
    (proj / "syn/report/csynth.rpt").write_text(
        "* Project:  secret_bench__proj\n* Date: today\n"
        "| TOP | in k (../../hls_eval_data/x/secret.cpp:14) |\n"
        "|- VITIS_LOOP_21_1 | 124 |\n"
    )
    (proj / ".autopilot/db/top-io-fe.xml").write_text('<arg src_type="ap_fixed"/>')
    (proj / ".autopilot/db/secret.pp.0.cpp").write_text("SECRET_SOURCE")
    reports = _collect_synthesis_reports(tmp_path)
    assert set(reports) == {"hls_reports/csynth.rpt", "hls_reports/top_io_frontend.xml"}
    text = "\n".join(reports.values())
    assert "VITIS_LOOP_21_1" in text and "ap_fixed" in text
    assert "secret" not in text.lower()
