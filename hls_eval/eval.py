import logging
import shutil
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from vllm import LLM

from hls_eval.data import BenchmarkCase
from hls_eval.llm import Model
from hls_eval.tools import CPPCompilerTool, VitisHLSSynthTool


class EvalThreadPools:
    def __init__(self, n_jobs_pool_llm: int, n_jobs_pool_tool: int) -> None:
        self.n_jobs_pool_llm = n_jobs_pool_llm
        self.n_jobs_pool_tool = n_jobs_pool_tool

        if n_jobs_pool_llm <= 1:
            raise ValueError("n_jobs_pool_llm must be greater than 1")
        if n_jobs_pool_tool <= 1:
            raise ValueError("n_jobs_pool_hls must be greater than 1")

        self.pool_llm = ThreadPoolExecutor(max_workers=n_jobs_pool_llm)
        self.pool_tool = ThreadPoolExecutor(max_workers=n_jobs_pool_tool)

    def shutdown(self):
        self.pool_llm.shutdown(wait=True)
        self.pool_tool.shutdown(wait=True)


class Evaluator(ABC):
    def __init__(
        self,
        cpp_compiler_tool: CPPCompilerTool,
        vitis_hls_tool: VitisHLSSynthTool,
        output_data_dir: Path,
    ) -> None:
        self.cpp_compiler_tool = cpp_compiler_tool
        self.vitis_hls_tool = vitis_hls_tool
        self.output_data_dir = output_data_dir
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
    ) -> None:
        raise NotImplementedError


class HLSGenerationZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        cpp_compiler_tool: CPPCompilerTool,
        vitis_hls_tool: VitisHLSSynthTool,
        output_data_dir: Path,
        prompt_task: str,
        prompt_system: str | None = None,
        n_samples: int = 1,
        temperature: float = 0.7,
    ) -> None:
        self.prompt_task = prompt_task
        self.prompt_system = prompt_system
        self.n_samples = n_samples
        self.temperature = temperature

        super().__init__(cpp_compiler_tool, vitis_hls_tool, output_data_dir)

    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
    ) -> None:
        model_name = model.name
        model_settings = model.settings
        llm = model.llm

        benchmark_case_name = benchmark_case.name

        eval_id = f"{benchmark_case_name}_{model_name}"

        self.logger.info(f"Running eval: {eval_id}")

        eval_dir = self.output_data_dir / eval_id
        if eval_dir.exists():
            self.logger.info(f"Removing existing eval dir: {eval_dir}")
            shutil.rmtree(eval_dir)
        eval_dir.mkdir(parents=True)

        # Run LLM
        # copy the design into the eval dir
        design_dir = eval_dir / "design"
        benchmark_case.copy_to(design_dir)


class HLSEditingZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        cpp_compiler_tool: CPPCompilerTool,
        vitis_hls_tool: VitisHLSSynthTool,
        output_data_dir: Path,
        prompt_task: str,
        prompt_system: str | None = None,
    ) -> None:
        self.prompt_task = prompt_task
        self.prompt_system = prompt_system

        super().__init__(cpp_compiler_tool, vitis_hls_tool, output_data_dir)

    def evaluate_design(
        self,
        design: BenchmarkCase,
        llm: LLM,
        pools: EvalThreadPools,
    ) -> None:
        raise NotImplementedError
