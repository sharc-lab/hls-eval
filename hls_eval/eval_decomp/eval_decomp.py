import shutil
from pathlib import Path

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools, Evaluator, serialize_eval_data
from hls_eval.llms import (
    Model,
    TAIPromptTooLong,
    TAITimeout,
    normalize_model_name,
)
from hls_eval.prompting import (
    approx_num_tokens,
    build_input_code_prompt_xml,
    extract_code_xml_from_llm_output,
)
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool


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
        if r.data_execution.return_code != 0:
            raise RuntimeError(
                f"Ground truth synthesis failed for {eval_id} with return code {r.data_execution.return_code}"
            )

        rtl_dir = sorted(ground_truth_build_dir.glob("**/solution*/syn/verilog"))
        if len(rtl_dir) != 1:
            raise RuntimeError(
                f"Expected exactly one RTL directory for {eval_id}, but found {len(rtl_dir)}"
            )
        rtl_files = sorted(rtl_dir[0].rglob("*.v")) + sorted(rtl_dir[0].rglob("*.sv"))
        print(
            f"Found {len(rtl_files)} RTL files for {eval_id}: {[str(f) for f in rtl_files]}"
        )

        # the idea is that we want to ask the LLM to look at the RTL output from the golden synthesis and try to reconstruct the original C/C++ code that produced it. This is a zero-shot decompilation task.
        # we then check if this C++ code is functionally equivalent to the original C++ code by synthesizing it and running the testbench.
