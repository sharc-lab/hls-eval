import shutil
from pathlib import Path

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools, Evaluator
from hls_eval.llms import Model, normalize_model_name
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool


class HLSGenerationZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        temperature: float | None = None,
    ) -> None:
        self.n_samples = n_samples
        self.temperature = temperature

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

        # for sample
