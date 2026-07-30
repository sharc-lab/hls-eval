import json
import shutil
import time
from pathlib import Path
from typing import Any

from llm import Response

from hls_eval.data import BenchmarkCase
from hls_eval.decomp.prompt_decomp import build_decompilation_prompt
from hls_eval.eval import EvalThreadPools, Evaluator, serialize_eval_data
from hls_eval.llms import (
    Model,
    TAIPromptTooLong,
    TAITimeout,
    normalize_model_name,
)
from hls_eval.prompting import (
    approx_num_tokens,
    extract_code_xml_from_llm_output,
)
from hls_eval.tools import ToolDataOutput, VitisHLSCSimTool, VitisHLSSynthTool


RTL_FILE_EXTENSIONS = {".dat", ".v", ".vhd", ".vhdl", ".vh", ".sv"}


def _serialize_tool_output(tool_output: ToolDataOutput) -> dict[str, Any]:
    return {
        "data_execution": {
            "return_code": tool_output.data_execution.return_code,
            "stdout": tool_output.data_execution.stdout,
            "stderr": tool_output.data_execution.stderr,
            "t0": tool_output.data_execution.t0,
            "t1": tool_output.data_execution.t1,
            "execution_time": tool_output.data_execution.execution_time,
            "timeout": tool_output.data_execution.timeout,
        },
        "data_tool": tool_output.data_tool or {},
    }


def _collect_synthesized_rtl(build_dir: Path) -> dict[str, str]:
    rtl_files: dict[str, str] = {}
    rtl_directories = sorted(
        directory
        for directory in build_dir.rglob("verilog")
        if directory.is_dir() and directory.parent.name == "syn"
    )
    rtl_directories.extend(
        sorted(
            directory
            for directory in build_dir.rglob("vhdl")
            if directory.is_dir() and directory.parent.name == "syn"
        )
    )

    for rtl_directory in rtl_directories:
        for rtl_file in sorted(path for path in rtl_directory.rglob("*") if path.is_file()):
            if rtl_file.suffix.lower() not in RTL_FILE_EXTENSIONS:
                continue
            relative_name = (Path("rtl") / rtl_file.relative_to(rtl_directory)).as_posix()
            if relative_name in rtl_files:
                raise ValueError(f"Duplicate synthesized RTL file name: {relative_name}")
            rtl_files[relative_name] = rtl_file.read_text(errors="replace")

    if not rtl_files:
        raise FileNotFoundError(
            f"No synthesized RTL files were found below {build_dir}"
        )
    return rtl_files


class HLSDecompZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        temperature: float | None = None,
        hls_clock_period_ns: float = 5.0,
        hls_fpga_part: str = "xczu9eg-ffvb1156-2-e",
        hls_compiler_defines: list[str] | None = None,
        hls_disable_auto_optimizations: bool = True,
        hls_unsafe_math: bool = True,
    ) -> None:
        if n_samples < 1:
            raise ValueError("n_samples must be at least 1")
        if hls_clock_period_ns <= 0:
            raise ValueError("hls_clock_period_ns must be positive")

        self.n_samples = n_samples
        self.temperature = temperature
        self.hls_clock_period_ns = hls_clock_period_ns
        self.hls_fpga_part = hls_fpga_part
        self.hls_compiler_defines = list(hls_compiler_defines or [])
        self.hls_disable_auto_optimizations = hls_disable_auto_optimizations
        self.hls_unsafe_math = hls_unsafe_math

        super().__init__(vitis_hls_tool_csim, vitis_hls_tool_synth, output_data_dir)

    def _base_eval_data(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        eval_id: str,
        ground_truth_synthesis_output: ToolDataOutput,
        rtl_file_names: list[str],
    ) -> dict[str, Any]:
        return {
            "eval_type": "hls_decomp_rtl_zero_shot",
            "eval_id": eval_id,
            "benchmark_case_name": benchmark_case.name,
            "benchmark_case_tags": benchmark_case.tags_all,
            "model_name": model.name,
            "model_name_normalized": normalize_model_name(model.name),
            "temperature": self.temperature,
            "n_samples": self.n_samples,
            "synthesis_parameters": {
                "hls_clock_period_ns": self.hls_clock_period_ns,
                "hls_clock_frequency_mhz": 1000.0 / self.hls_clock_period_ns,
                "hls_fpga_part": self.hls_fpga_part,
                "hls_compiler_defines": self.hls_compiler_defines,
                "hls_top_function": benchmark_case.top_fn,
                "hls_flow_target": "vivado",
                "hls_disable_auto_optimizations": (
                    self.hls_disable_auto_optimizations
                ),
                "hls_unsafe_math": self.hls_unsafe_math,
            },
            "ground_truth_pass_synth": (
                ground_truth_synthesis_output.data_execution.return_code == 0
            ),
            "ground_truth_vitis_hls_tool_out": _serialize_tool_output(
                ground_truth_synthesis_output
            ),
            "rtl_files": rtl_file_names,
            "pass_compile": False,
            "pass_synth": False,
        }

    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
        **kwargs,
    ) -> None:
        model_name_normalized = normalize_model_name(model.name)
        eval_id = f"{benchmark_case.name}__{model_name_normalized}"
        eval_dir_top = self.output_data_dir / eval_id
        if eval_dir_top.exists():
            self.logger.info(f"Removing existing top eval dir: {eval_dir_top}")
            shutil.rmtree(eval_dir_top)
        eval_dir_top.mkdir(parents=True)

        synthesis_source_files = [
            source_file
            for source_file in benchmark_case.source_files
            if source_file != benchmark_case.tb_file
        ]
        ground_truth_build_dir = eval_dir_top / "ground_truth_build"
        ground_truth_build_dir.mkdir()
        self.logger.info(f"[{eval_id}] Synthesizing reference design to RTL")
        ground_truth_synthesis_output = pools.pool_synth.submit(
            self.vitis_hls_tool.run,
            ground_truth_build_dir,
            synthesis_source_files,
            build_name=eval_id,
            hls_top_function=benchmark_case.top_fn,
            hls_fpga_part=self.hls_fpga_part,
            hls_clock_period_ns=self.hls_clock_period_ns,
            hls_flow_target="vivado",
            hls_disable_auto_optimizations=self.hls_disable_auto_optimizations,
            hls_unsafe_math=self.hls_unsafe_math,
            hls_compiler_defines=self.hls_compiler_defines,
        ).result()

        rtl_files: dict[str, str] = {}
        ground_truth_error: str | None = None
        if ground_truth_synthesis_output.data_execution.return_code == 0:
            try:
                rtl_files = _collect_synthesized_rtl(ground_truth_build_dir)
            except (FileNotFoundError, ValueError) as error:
                ground_truth_error = str(error)
        else:
            ground_truth_error = "Ground-truth Vitis HLS synthesis failed"

        prompt = None
        if ground_truth_error is None:
            prompt = build_decompilation_prompt(
                rtl_files,
                benchmark_case.top_fn,
                self.hls_clock_period_ns,
                self.hls_fpga_part,
                self.hls_compiler_defines,
                self.hls_disable_auto_optimizations,
                self.hls_unsafe_math,
            )

        for sample_idx in range(self.n_samples):
            eval_dir = eval_dir_top / f"sample__{sample_idx}"
            eval_dir.mkdir(parents=True)
            eval_data = self._base_eval_data(
                benchmark_case,
                model,
                eval_id,
                ground_truth_synthesis_output,
                list(rtl_files),
            )

            if ground_truth_error is not None:
                eval_data["ground_truth_error"] = ground_truth_error
                serialize_eval_data(eval_id, eval_dir, eval_data)
                continue

            assert prompt is not None
            eval_data["prompt"] = prompt
            (eval_dir / "raw_llm_prompt.txt").write_text(prompt)

            def call_model() -> tuple[
                Response | None, str | None, bool, bool, float, float
            ]:
                t0 = time.monotonic()
                try:
                    response = model.llm.prompt(
                        prompt=prompt,
                        stream=False,
                        temperature=self.temperature,
                    )
                    response._force()
                    return (
                        response,
                        response.text(),
                        False,
                        False,
                        t0,
                        time.monotonic(),
                    )
                except TAITimeout:
                    return None, None, True, False, t0, time.monotonic()
                except TAIPromptTooLong:
                    return None, None, False, True, t0, time.monotonic()

            self.logger.info(
                f"[{eval_id}] Calling model with approximately "
                f"{approx_num_tokens(prompt)} prompt tokens"
            )
            (
                response,
                response_text,
                model_timeout,
                prompt_too_long,
                llm_t0,
                llm_t1,
            ) = pools.pool_llm.submit(call_model).result()
            eval_data["model_timeout"] = model_timeout
            eval_data["prompt_too_long"] = prompt_too_long
            eval_data["llm_execution_time"] = {
                "t0": llm_t0,
                "t1": llm_t1,
                "execution_time": llm_t1 - llm_t0,
            }

            if response is None or response_text is None:
                serialize_eval_data(eval_id, eval_dir, eval_data)
                continue

            if response.response_json is not None:
                eval_data["response_json"] = response.response_json
            eval_data["raw_output"] = response_text
            (eval_dir / "raw_llm_output.txt").write_text(response_text)

            try:
                generated_code = extract_code_xml_from_llm_output(response_text)
                if set(generated_code) != {"decompiled.cpp"}:
                    raise ValueError(
                        "Expected exactly one OUTPUT_CODE named decompiled.cpp"
                    )
                decompiled_code = generated_code["decompiled.cpp"].strip() + "\n"
                eval_data["generated_code"] = {
                    "decompiled.cpp": decompiled_code,
                }
                eval_data["can_parse_output"] = True
            except (IndexError, TypeError, ValueError) as error:
                eval_data["can_parse_output"] = False
                eval_data["output_parse_error"] = str(error)
                serialize_eval_data(eval_id, eval_dir, eval_data)
                continue

            design_generated_dir = eval_dir / "design_generated"
            design_generated_dir.mkdir()
            generated_source = design_generated_dir / "decompiled.cpp"
            generated_source.write_text(decompiled_code)

            compile_check_main = eval_dir / "compile_check_main.cpp"
            compile_check_main.write_text("int main() { return 0; }\n")
            compile_build_dir = eval_dir / "compile_build"
            synth_build_dir = eval_dir / "synth_build"
            compile_build_dir.mkdir()
            synth_build_dir.mkdir()

            compile_future = pools.pool_csim.submit(
                self.cpp_compiler_tool.run,
                compile_build_dir,
                [generated_source, compile_check_main],
                build_name=f"{eval_id}__sample_{sample_idx}__compile",
                hls_top_function=benchmark_case.top_fn,
                hls_fpga_part=self.hls_fpga_part,
                hls_clock_period_ns=self.hls_clock_period_ns,
                hls_flow_target="vivado",
            )
            synth_future = pools.pool_synth.submit(
                self.vitis_hls_tool.run,
                synth_build_dir,
                [generated_source],
                build_name=f"{eval_id}__sample_{sample_idx}__synth",
                hls_top_function=benchmark_case.top_fn,
                hls_fpga_part=self.hls_fpga_part,
                hls_clock_period_ns=self.hls_clock_period_ns,
                hls_flow_target="vivado",
                hls_disable_auto_optimizations=self.hls_disable_auto_optimizations,
                hls_unsafe_math=self.hls_unsafe_math,
                hls_compiler_defines=self.hls_compiler_defines,
            )

            compile_output, compile_run_output = compile_future.result()
            synth_output = synth_future.result()
            eval_data["c_compile_out"] = _serialize_tool_output(compile_output)
            if compile_run_output is not None:
                eval_data["c_run_out"] = _serialize_tool_output(compile_run_output)
            eval_data["vitis_hls_tool_out"] = _serialize_tool_output(synth_output)
            eval_data["pass_compile"] = (
                compile_output.data_execution.return_code == 0
            )
            eval_data["pass_synth"] = synth_output.data_execution.return_code == 0
            serialize_eval_data(eval_id, eval_dir, eval_data)

        all_eval_data = {
            sample_idx: json.loads(
                (
                    eval_dir_top
                    / f"sample__{sample_idx}"
                    / "single_eval_data.json"
                ).read_text()
            )
            for sample_idx in range(self.n_samples)
        }
        (eval_dir_top / "all_eval_data.json").write_text(
            json.dumps(all_eval_data, indent=4)
        )
