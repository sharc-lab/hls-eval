import itertools
import json
import logging
import shutil
import time
from abc import ABC, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from threading import BoundedSemaphore
from typing import Any

from joblib import Parallel, delayed
from llm import Response

from hls_eval.data import BenchmarkCase
from hls_eval.llms import Model, TAITimeout, normalize_model_name
from hls_eval.prompting import approx_num_tokens, extract_code_xml_from_llm_outout
from hls_eval.prompts import build_prompt_gen_zero_shot
from hls_eval.rate_limit import RemoteLLMRateLimit
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool


class EvalThreadPools:
    def __init__(
        self,
        n_jobs_pool_llm: int,
        n_jobs_pool_csim: int,
        n_jobs_pool_synth: int,
        tokens_per_minute: int | None = None,
        requests_per_minute: int | None = None,
    ) -> None:
        self.n_jobs_pool_llm = n_jobs_pool_llm
        self.n_jobs_pool_csim = n_jobs_pool_csim
        self.n_jobs_pool_synth = n_jobs_pool_synth

        self.tokens_per_minute = tokens_per_minute
        self.requests_per_minute = requests_per_minute

        if n_jobs_pool_llm <= 1:
            raise ValueError("n_jobs_pool_llm must be greater than 1")
        if n_jobs_pool_csim <= 1:
            raise ValueError("n_jobs_pool_csim must be greater than 1")
        if n_jobs_pool_synth <= 1:
            raise ValueError("n_jobs_pool_synth must be greater than 1")

        self.llm_sema = BoundedSemaphore(n_jobs_pool_llm)

        self.llm_rate_limiter = RemoteLLMRateLimit(
            tokens_per_minute, requests_per_minute
        )

        self.pool_llm = ThreadPoolExecutor(max_workers=n_jobs_pool_llm)
        self.pool_csim = ThreadPoolExecutor(max_workers=n_jobs_pool_csim)
        self.pool_synth = ThreadPoolExecutor(max_workers=n_jobs_pool_synth)

    def shutdown(self):
        self.pool_llm.shutdown(wait=True)
        self.pool_csim.shutdown(wait=True)
        self.pool_synth.shutdown(wait=True)


class Evaluator(ABC):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
    ) -> None:
        self.cpp_compiler_tool = vitis_hls_tool_csim
        self.vitis_hls_tool = vitis_hls_tool_synth
        self.output_data_dir = output_data_dir
        self.logger = logging.getLogger(__name__)

    @abstractmethod
    def evaluate_design(
        self,
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
        **kwargs,
    ) -> None:
        raise NotImplementedError

    def build_eval_combos(
        self,
        benchmark_cases: list[BenchmarkCase],
        models: list[Model],
    ) -> list[tuple[BenchmarkCase, Model]]:
        combos = list(itertools.product(benchmark_cases, models))
        combos = sorted(combos, key=lambda x: (x[0].name, x[1].name))
        return combos

    def evaluate_designs(
        self,
        benchmark_cases: list[BenchmarkCase],
        models: list[Model],
        n_jobs: int = 1,
        n_jobs_pool_llm: int = 1,
        n_jobs_pool_csim: int = 1,
        n_jobs_pool_synth: int = 1,
        tokens_per_minute: int | None = None,
        requests_per_minute: int | None = None,
        **kwargs,
    ) -> None:
        combos: list[tuple[BenchmarkCase, Model]] = self.build_eval_combos(
            benchmark_cases, models
        )
        pools = EvalThreadPools(
            n_jobs_pool_llm,
            n_jobs_pool_csim,
            n_jobs_pool_synth,
            tokens_per_minute,
            requests_per_minute,
        )
        Parallel(n_jobs=n_jobs, backend="threading")(
            delayed(self.evaluate_design)(design, model, pools)
            for design, model in combos
        )
        pools.shutdown()

    def evaluate_design_model_paris(
        self,
        design_model_pairs: list[tuple[BenchmarkCase, Model]],
        n_jobs: int = 1,
        n_jobs_pool_llm: int = 1,
        n_jobs_pool_csim: int = 1,
        n_jobs_pool_synth: int = 1,
        tokens_per_minute: int | None = None,
        requests_per_minute: int | None = None,
        **kwargs,
    ):
        pools = EvalThreadPools(
            n_jobs_pool_llm,
            n_jobs_pool_csim,
            n_jobs_pool_synth,
            tokens_per_minute,
            requests_per_minute,
        )
        Parallel(n_jobs=n_jobs, backend="threading")(
            delayed(self.evaluate_design)(design, model, pools)
            for design, model in design_model_pairs
        )
        pools.shutdown()


def serialize_eval_data(eval_id: str, eval_output_dir: Path, single_eval_data: dict):
    # print(f"[{eval_id}] Saving eval data to json...")
    single_eval_data_json = json.dumps(single_eval_data, indent=4)
    (eval_output_dir / "single_eval_data.json").write_text(str(single_eval_data_json))


class HLSGenerationZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        # prompt_task: str | None = None,
        # prompt_system: str | None = None,
        n_samples: int = 1,
        temperature: float = 0.7,
    ) -> None:
        # self.prompt_task = prompt_task
        # self.prompt_system = prompt_system
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

        for sample_idx in range(self.n_samples):
            eval_data: dict[str, Any] = {}

            eval_data["eval_type"] = "hls_gen_zero_shot"
            eval_data["eval_id"] = eval_id
            eval_data["benchmark_case_name"] = benchmark_case_name
            eval_data["benchmark_case_tags"] = benchmark_case.tags_all
            eval_data["model_name"] = model_name
            eval_data["model_name_normalized"] = model_name_normalized

            eval_data["temperature"] = self.temperature
            eval_data["n_samples"] = self.n_samples

            self.logger.info(f"[{eval_id}] Running eval...")

            eval_dir = eval_dir_top / f"sample__{sample_idx}"
            if eval_dir.exists():
                self.logger.info(f"Removing existing sample eval dir: {eval_dir}")
                shutil.rmtree(eval_dir)
            eval_dir.mkdir(parents=True)

            design_dir = eval_dir / "design"
            benchmark_case = benchmark_case.copy_to(design_dir)

            assert len(benchmark_case.h_files) == 1
            design_header = benchmark_case.h_files[0]
            design_tb = benchmark_case.tb_file
            design_description = benchmark_case.kernel_description_fp

            prompt = build_prompt_gen_zero_shot(
                design_description,
                design_tb,
                design_header,
            )
            eval_data["prompt"] = prompt
            (eval_dir / "raw_llm_prompt.txt").write_text(prompt)

            n_tokens_guess = approx_num_tokens(prompt)

            llm_pool = pools.pool_llm

            llm = model.llm

            t0 = time.monotonic()

            def call_model(
                prompt,
            ) -> tuple[
                Response | None, str | None, dict | None, bool, float, float, float
            ]:
                print(f"[{eval_id}] Calling model...")
                print(f"[{eval_id}] Waiting for {n_tokens_guess} tokens")
                # llm_rate_limiter.wait_for(n_tokens_guess)
                t_0 = time.monotonic()
                r: Response | None = None
                r_text: str | None = None
                r_json: dict | None = None
                try:
                    r = llm.prompt(
                        prompt=prompt,
                        stream=False,
                        temperature=self.temperature,
                    )
                    r._force()
                    r_json = r.json()
                    r_text = r.text()
                    t1 = time.monotonic()
                    dt = t1 - t_0
                    model_timeout = False
                except TAITimeout:
                    t1 = time.monotonic()
                    dt = t1 - t_0
                    model_timeout = True

                return r, r_text, r_json, model_timeout, t_0, t1, dt

            future_llm = llm_pool.submit(call_model, prompt)
            r, r_text, r_json, model_timeout, t0, t1, dt = future_llm.result()

            eval_data["model_timeout"] = model_timeout
            eval_data["llm_execution_time"] = {"t0": t0, "t1": t1, "execution_time": dt}

            if model_timeout:
                serialize_eval_data(eval_id, eval_dir, eval_data)
                return

            assert r is not None
            assert r_text is not None

            if r.response_json is not None:
                eval_data["response_json"] = r.response_json

            eval_data["raw_output"] = str(r_text)
            (eval_dir / "raw_llm_output.txt").write_text(r_text)

            print(f"[{eval_id}] Extracting code from output...")
            try:
                generated_code = extract_code_xml_from_llm_outout(r_text)
                assert len(generated_code) == 1
                generated_code_file_name = list(generated_code.keys())[0]
                assert generated_code_file_name.endswith(".cpp")
                eval_data["generated_code"] = generated_code
                eval_data["can_parse_output"] = True
            except Exception:
                print(f"[{eval_id}] Error extracting code from LLM output")
                eval_data["can_parse_output"] = False
                serialize_eval_data(eval_id, eval_dir, eval_data)
                return

            # make a design_generated dir
            design_generated_dir = eval_dir / "design_generated"
            design_generated_dir.mkdir()

            # copy the design files
            shutil.copy(design_header, design_generated_dir)
            shutil.copy(design_tb, design_generated_dir)
            shutil.copy(design_description, design_generated_dir)

            # write the generated code to a file
            for file_name, code in generated_code.items():
                (design_generated_dir / f"{file_name}").write_text(code)

            build_dir = eval_dir / "build"
            build_dir.mkdir(parents=True, exist_ok=True)

            build_dir_source_files = sorted(
                list(design_generated_dir.glob("*.cpp"))
                + list(design_generated_dir.glob("*.h"))
            )
            build_dir_not_source_files = sorted(
                list(set(design_generated_dir.glob("*")) - set(build_dir_source_files))
            )

            pool_csim = pools.pool_csim

            print(f"[{eval_id}] Compiling and running the LLM version of the design...")

            future_tool_cpp = pool_csim.submit(
                self.cpp_compiler_tool.run,
                build_dir,
                build_dir_source_files,
                build_dir_not_source_files,
                eval_id,
            )

            c_compile_out, c_run_out = future_tool_cpp.result()

            eval_data["c_compile_out"] = {}
            eval_data["c_compile_out"]["data_execution"] = {
                "return_code": c_compile_out.data_execution.return_code,
                "stdout": c_compile_out.data_execution.stdout,
                "stderr": c_compile_out.data_execution.stderr,
                "t0": c_compile_out.data_execution.t0,
                "t1": c_compile_out.data_execution.t1,
                "execution_time": c_compile_out.data_execution.execution_time,
                "timeout": c_compile_out.data_execution.timeout,
            }

            print(
                f"[{eval_id}] Testbench compile return code: {c_compile_out.data_execution.return_code}"
            )

            if c_run_out:
                eval_data["c_run_out"] = {}
                eval_data["c_run_out"]["data_execution"] = {
                    "return_code": c_run_out.data_execution.return_code,
                    "stdout": c_run_out.data_execution.stdout,
                    "stderr": c_run_out.data_execution.stderr,
                    "t0": c_run_out.data_execution.t0,
                    "t1": c_run_out.data_execution.t1,
                    "execution_time": c_run_out.data_execution.execution_time,
                    "timeout": c_run_out.data_execution.timeout,
                }

                print(
                    f"[{eval_id}] Testbench return code: {c_run_out.data_execution.return_code}"
                )

            pool_synth = pools.pool_synth

            print(f"[{eval_id}] Synthesizing the LLM version of the design...")
            top_function_name = benchmark_case.top_fn

            future_tool_hls = pool_synth.submit(
                self.vitis_hls_tool.run,
                build_dir,
                build_dir_source_files,
                build_name=eval_id,
                hls_top_function=top_function_name,
            )
            vitis_hls_tool_output = future_tool_hls.result()

            eval_data["vitis_hls_tool_out"] = {}
            eval_data["vitis_hls_tool_out"]["data_execution"] = {
                "return_code": vitis_hls_tool_output.data_execution.return_code,
                "stdout": vitis_hls_tool_output.data_execution.stdout,
                "stderr": vitis_hls_tool_output.data_execution.stderr,
                "t0": vitis_hls_tool_output.data_execution.t0,
                "t1": vitis_hls_tool_output.data_execution.t1,
                "execution_time": vitis_hls_tool_output.data_execution.execution_time,
                "timeout": vitis_hls_tool_output.data_execution.timeout,
            }
            eval_data["vitis_hls_tool_out"]["data_tool"] = {}
            if vitis_hls_tool_output.data_tool:
                for k, v in vitis_hls_tool_output.data_tool.items():
                    eval_data["vitis_hls_tool_out"]["data_tool"][k] = v
            print(
                f"[{eval_id}] Vitis HLS return code: {vitis_hls_tool_output.data_execution.return_code}"
            )

            serialize_eval_data(eval_id, eval_dir, eval_data)

        all_eval_data = {}
        for sample_idx in range(self.n_samples):
            sample_eval_data_fp = (
                eval_dir_top / f"sample__{sample_idx}" / "single_eval_data.json"
            )
            sample_eval_data = json.loads(sample_eval_data_fp.read_text())
            all_eval_data[sample_idx] = sample_eval_data
        all_eval_data_fp = eval_dir_top / "all_eval_data.json"
        all_eval_data_fp.write_text(json.dumps(all_eval_data, indent=4))


class HLSEditingZeroShotEvaluator(Evaluator):
    def __init__(
        self,
        cpp_compiler_tool: VitisHLSCSimTool,
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
        benchmark_case: BenchmarkCase,
        model: Model,
        pools: EvalThreadPools,
        **kwargs,
    ) -> None:
        raise NotImplementedError
