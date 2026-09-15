import json
import shutil
import time
from dataclasses import asdict
from pathlib import Path
from typing import Any

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
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool


DEIDENTIFIED_KERNEL_NAME = "kernel_KERNEL_NAME"


def _deidentify_rtl(rtl_files: dict[str, str], top_function: str) -> dict[str, str]:
    """Rename the kernel everywhere, preserving generated helper suffixes."""
    deidentified = {}
    for name, content in rtl_files.items():
        renamed = name.replace(top_function, DEIDENTIFIED_KERNEL_NAME)
        if renamed in deidentified:
            raise ValueError(f"Deidentified RTL filename collision: {renamed}")
        deidentified[renamed] = content.replace(top_function, DEIDENTIFIED_KERNEL_NAME)
    return deidentified


def _write_rtl_files(directory: Path, rtl_files: dict[str, str]) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    for name, content in rtl_files.items():
        destination = directory / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(content)


class HLSDecompilationZeroShotEvaluator(Evaluator):
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

    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
        **kwargs,
    ) -> None:
        model_name: str = model.name
        model_name_normalized = normalize_model_name(model_name)
        benchmark_case_name = benchmark_case.name
        eval_id = f"{benchmark_case_name}__{model_name_normalized}"

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
        synthesis_future = pools.pool_synth.submit(
            self.vitis_hls_tool.run,
            ground_truth_build_dir,
            synthesis_source_files,
            build_name=eval_id,
            hls_top_function=benchmark_case.top_fn,
            hls_fpga_part=self.hls_fpga_part,
            hls_clock_period_ns=self.hls_clock_period_ns,
            hls_disable_auto_optimizations=self.hls_disable_auto_optimizations,
            hls_unsafe_math=self.hls_unsafe_math,
            hls_compiler_defines=self.hls_compiler_defines,
        )
        r = synthesis_future.result()
        if r.data_execution.return_code != 0 or r.data_execution.timeout:
            raise RuntimeError(
                f"Ground truth synthesis failed for {eval_id} with return code {r.data_execution.return_code}"
            )

        rtl_dir = sorted(ground_truth_build_dir.glob("**/solution*/syn/verilog"))
        if len(rtl_dir) != 1:
            raise RuntimeError(
                f"Expected exactly one RTL directory for {eval_id}, but found {len(rtl_dir)}"
            )
        # Include ROM contents and included headers as well as module definitions.
        rtl_files = {
            file.relative_to(rtl_dir[0]).as_posix(): file.read_text()
            for file in sorted(rtl_dir[0].rglob("*"))
            if file.is_file()
            and file.suffix.lower() in {".v", ".sv", ".vh", ".svh", ".dat", ".mem"}
        }
        if not any(Path(name).suffix.lower() in {".v", ".sv"} for name in rtl_files):
            raise RuntimeError(f"No synthesized RTL modules found for {eval_id}")
        self.logger.info(f"[{eval_id}] Found {len(rtl_files)} RTL input files")

        rtl_files_deidentified = _deidentify_rtl(rtl_files, benchmark_case.top_fn)
        _write_rtl_files(eval_dir_top / "rtl_synth", rtl_files)
        _write_rtl_files(
            eval_dir_top / "rtl_synth_deidentified", rtl_files_deidentified
        )
        prompt = build_decompilation_prompt(
            rtl_files_deidentified,
            DEIDENTIFIED_KERNEL_NAME,
            self.hls_clock_period_ns,
            self.hls_fpga_part,
            self.hls_compiler_defines,
            self.hls_disable_auto_optimizations,
            self.hls_unsafe_math,
        )
        hls_parameters: dict[str, Any] = {
            "hls_top_function": benchmark_case.top_fn,
            "hls_fpga_part": self.hls_fpga_part,
            "hls_clock_period_ns": self.hls_clock_period_ns,
            "hls_compiler_defines": self.hls_compiler_defines,
        }
        all_eval_data = {}
        for sample_idx in range(self.n_samples):
            eval_dir = eval_dir_top / f"sample__{sample_idx}"
            eval_dir.mkdir()
            eval_data: dict[str, Any] = {
                "eval_type": "hls_decomp_rtl_zero_shot",
                "eval_id": eval_id,
                "sample_idx": sample_idx,
                "benchmark_case_name": benchmark_case_name,
                "benchmark_case_tags": benchmark_case.tags_all,
                "model_name": model_name,
                "model_name_normalized": model_name_normalized,
                "temperature": self.temperature,
                "n_samples": self.n_samples,
                "synthesis_parameters": {
                    **hls_parameters,
                    "hls_disable_auto_optimizations": self.hls_disable_auto_optimizations,
                    "hls_unsafe_math": self.hls_unsafe_math,
                },
                "ground_truth_pass_synth": True,
                "ground_truth_vitis_hls_tool_out": asdict(r),
                "rtl_files": list(rtl_files),
                "rtl_files_deidentified": list(rtl_files_deidentified),
                "rtl_deidentification": {
                    "original_kernel_name": benchmark_case.top_fn,
                    "deidentified_kernel_name": DEIDENTIFIED_KERNEL_NAME,
                },
                "prompt": prompt,
                "model_timeout": False,
                "prompt_too_long": False,
                "can_parse_output": False,
                "pass_compile": False,
                "pass_run": False,
                "pass_synth": False,
                "pass_all": False,
            }
            (eval_dir / "raw_llm_prompt.txt").write_text(prompt)

            def call_model():
                t0 = time.monotonic()
                try:
                    options = {}
                    if self.temperature is not None:
                        options["temperature"] = self.temperature
                    response = model.llm.prompt(prompt=prompt, stream=False, **options)
                    response._force()
                    return response, response.text()
                except TAITimeout:
                    eval_data["model_timeout"] = True
                    return None, None
                except TAIPromptTooLong:
                    eval_data["prompt_too_long"] = True
                    return None, None
                finally:
                    t1 = time.monotonic()
                    eval_data["llm_execution_time"] = {
                        "t0": t0,
                        "t1": t1,
                        "execution_time": t1 - t0,
                    }

            self.logger.info(
                f"[{eval_id}] Sample {sample_idx}: requesting decompilation "
                f"with approximately {approx_num_tokens(prompt)} prompt tokens"
            )
            response, response_text = pools.pool_llm.submit(call_model).result()
            if response is not None and response_text is not None:
                if response.response_json is not None:
                    eval_data["response_json"] = response.response_json
                eval_data["raw_output"] = response_text
                (eval_dir / "raw_llm_output.txt").write_text(response_text)
                try:
                    generated_code = extract_code_xml_from_llm_output(response_text)
                    if set(generated_code) != {"decompiled.cpp"}:
                        raise ValueError(
                            "Expected one OUTPUT_CODE named decompiled.cpp"
                        )
                    if not generated_code["decompiled.cpp"].strip():
                        raise ValueError("Generated C++ code is empty")
                    # The model sees only the anonymous name; restore the original
                    # name locally so synthesis and the untouched testbench agree.
                    generated_code["decompiled.cpp"] = generated_code[
                        "decompiled.cpp"
                    ].replace(DEIDENTIFIED_KERNEL_NAME, benchmark_case.top_fn)
                    eval_data["generated_code"] = generated_code
                    eval_data["can_parse_output"] = True
                except (IndexError, TypeError, ValueError) as error:
                    eval_data["output_parse_error"] = str(error)
                else:
                    design_generated_dir = eval_dir / "design_generated"
                    design_generated_dir.mkdir()
                    generated_source = design_generated_dir / "decompiled.cpp"
                    generated_source.write_text(generated_code["decompiled.cpp"])

                    # Keep the original testbench and its headers/data for validation.
                    # Original implementation files are never compiled with the candidate.
                    validation_dir = eval_dir / "validation"
                    validation_dir.mkdir()
                    validation_sources = []
                    for source in [*benchmark_case.h_files, benchmark_case.tb_file]:
                        destination = validation_dir / source.name
                        shutil.copy(source, destination)
                        validation_sources.append(destination)
                    validation_data = []
                    for source in benchmark_case.tb_data_files:
                        destination = validation_dir / source.relative_to(
                            benchmark_case.design_dir
                        )
                        destination.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy(source, destination)
                        validation_data.append(destination)

                    compile_build_dir = eval_dir / "compile_build"
                    synth_build_dir = eval_dir / "synth_build"
                    compile_build_dir.mkdir()
                    synth_build_dir.mkdir()
                    build_name = f"{eval_id}__sample_{sample_idx}"
                    compile_future = pools.pool_csim.submit(
                        self.cpp_compiler_tool.run,
                        compile_build_dir,
                        [generated_source, *validation_sources],
                        aux_files=validation_data,
                        build_name=build_name,
                        **hls_parameters,
                    )
                    synth_future = pools.pool_synth.submit(
                        self.vitis_hls_tool.run,
                        synth_build_dir,
                        [generated_source],
                        build_name=build_name,
                        hls_disable_auto_optimizations=self.hls_disable_auto_optimizations,
                        hls_unsafe_math=self.hls_unsafe_math,
                        **hls_parameters,
                    )
                    compile_output, run_output = compile_future.result()
                    synth_output = synth_future.result()
                    eval_data["c_compile_out"] = asdict(compile_output)
                    eval_data["pass_compile"] = (
                        compile_output.data_execution.return_code == 0
                        and not compile_output.data_execution.timeout
                    )
                    if run_output is not None:
                        eval_data["c_run_out"] = asdict(run_output)
                        eval_data["pass_run"] = (
                            eval_data["pass_compile"]
                            and run_output.data_execution.return_code == 0
                            and not run_output.data_execution.timeout
                        )
                    eval_data["vitis_hls_tool_out"] = asdict(synth_output)
                    eval_data["pass_synth"] = (
                        synth_output.data_execution.return_code == 0
                        and not synth_output.data_execution.timeout
                    )
                    eval_data["pass_all"] = (
                        eval_data["pass_run"] and eval_data["pass_synth"]
                    )

            serialize_eval_data(eval_id, eval_dir, eval_data)
            all_eval_data[sample_idx] = eval_data

        (eval_dir_top / "all_eval_data.json").write_text(
            json.dumps(all_eval_data, indent=4)
        )
