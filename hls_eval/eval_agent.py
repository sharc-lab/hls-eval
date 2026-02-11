import json
import logging
import os
import shutil
import time
from pathlib import Path
from typing import Any

import yaml
from llm_openrouter import OpenRouterChat

from hls_eval.agent_trace_render import render_trace_to_html
from hls_eval.prompts import build_prompt_gen_agentic

os.environ["MSWEA_SILENT_STARTUP"] = "1"
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.docker import DockerEnvironment
from minisweagent.models.openrouter_model import OpenRouterModel

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools, Evaluator, serialize_eval_data
from hls_eval.llms import Model, normalize_model_name
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool

DIR_CURRENT = Path(__file__).parent

fp_config_agent = DIR_CURRENT / "swe_mini_agent_configs" / "main.yaml"
config_loaded_agent = yaml.safe_load(fp_config_agent.read_text())


class HLSGenerationAgentEvaluator(Evaluator):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        temperature: float = 0.7,
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

        for sample_idx in range(self.n_samples):
            eval_data: dict[str, Any] = {}

            eval_data["eval_type"] = "hls_gen_agentic"
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
            design_kernel = benchmark_case.kernel_fp

            # make an agent run dir and copy the design files to it
            agent_run_dir = eval_dir / "agent_run_dir"
            agent_run_dir.mkdir()

            shutil.copy(design_description, agent_run_dir)
            shutil.copy(design_header, agent_run_dir)
            shutil.copy(design_tb, agent_run_dir)

            prompt = build_prompt_gen_agentic(
                fn_design_description=design_description.name,
                fn_design_h=design_header.name,
                fn_design_tb=design_tb.name,
                fn_design_kernel=design_kernel.name,
            )
            eval_data["prompt"] = prompt
            (eval_dir / "raw_agent_prompt.txt").write_text(prompt)

            silent_logger = logging.getLogger("silent_logger")
            silent_logger.addHandler(logging.NullHandler())
            silent_logger.propagate = False

            env = DockerEnvironment(
                logger=silent_logger,
                image="python:3.12",
                cwd="/work",
                run_args=[
                    "--rm",
                    "--mount",
                    f"type=bind,source={str(agent_run_dir.resolve().absolute())},target=/work",
                ],
                **config_loaded_agent.get("environment", {}),
            )

            os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"

            if isinstance(model.llm, OpenRouterChat):
                copy_model_name = model.llm.model_name

                model_kwargs = {}
                if "provider" in model.settings:
                    model_kwargs["provider"] = {
                        "only": [model.settings["provider"]],
                    }

                copy_api_key = model.llm.key
                if copy_api_key is None:
                    raise ValueError(f"API key not found for model {model_name}")
                os.environ["OPENROUTER_API_KEY"] = copy_api_key

                model_for_agent = OpenRouterModel(
                    model_name=copy_model_name,
                    model_kwargs=model_kwargs,
                    cost_tracking="ignore_errors",
                )
            else:
                raise NotImplementedError(
                    f"Model {model_name} is not an OpenRouter model, only OpenRouter models are supported for agent evals right now."
                )

            agent = DefaultAgent(
                model=model_for_agent,
                env=env,
                **config_loaded_agent.get("agent", {}),
            )

            def run_agent_attempt():
                agent_submitted = False
                agent_limit_exceeded = False

                t0 = time.monotonic()
                result = agent.run(prompt)
                t1 = time.monotonic()

                result_condition_name, result_condition_description = result

                if result_condition_name == "Submitted":
                    agent_submitted = True
                    agent_limit_exceeded = False
                elif result_condition_name == "LimitsExceeded":
                    agent_submitted = False
                    agent_limit_exceeded = True
                else:
                    raise ValueError(
                        f"Unknown agent result condition:\n{result_condition_name}\n{result_condition_description}"
                    )

                dt = t1 - t0
                return agent_submitted, agent_limit_exceeded, t0, t1, dt

            pool_agent = pools.pool_agent

            future_agent = pool_agent.submit(run_agent_attempt)
            agent_submitted, agent_limit_exceeded, t0, t1, dt = future_agent.result()

            eval_data["agent_execution_time"] = {
                "t0": t0,
                "t1": t1,
                "execution_time": dt,
            }
            eval_data["agent_submitted"] = agent_submitted
            eval_data["agent_limit_exceeded"] = agent_limit_exceeded

            agent_trace = agent.messages
            eval_data["agent_trace"] = agent_trace

            trace_json = json.dumps(agent_trace, indent=4)
            fp_trace_json = eval_dir / "trace.json"
            fp_trace_json.write_text(trace_json)

            trace_html = render_trace_to_html(agent_trace)
            fp_trace_html = eval_dir / "trace.html"
            fp_trace_html.write_text(trace_html)

            if agent_limit_exceeded is True:
                serialize_eval_data(eval_id, eval_dir, eval_data)
                continue

            can_find_kernel_file = None
            has_modifed_testbench = None
            has_modified_header = None

            fp_kernel_in_agent_run_dir = agent_run_dir / design_kernel.name
            if not fp_kernel_in_agent_run_dir.exists():
                can_find_kernel_file = False
            else:
                can_find_kernel_file = True

            fp_testbench_in_agent_run_dir = agent_run_dir / design_tb.name
            # check to see if the contents is the same as the one in the design dir
            if not fp_testbench_in_agent_run_dir.exists():
                has_modifed_testbench = True
            else:
                txt_testbench_in_agent_run_dir = (
                    fp_testbench_in_agent_run_dir.read_text()
                )
                txt_testbench_in_design_dir = design_tb.read_text()
                if txt_testbench_in_agent_run_dir != txt_testbench_in_design_dir:
                    has_modifed_testbench = True
                else:
                    has_modifed_testbench = False

            fp_header_in_agent_run_dir = agent_run_dir / design_header.name
            if not fp_header_in_agent_run_dir.exists():
                has_modified_header = True
            else:
                txt_header_in_agent_run_dir = fp_header_in_agent_run_dir.read_text()
                txt_header_in_design_dir = design_header.read_text()
                if txt_header_in_agent_run_dir != txt_header_in_design_dir:
                    has_modified_header = True
                else:
                    has_modified_header = False

            assert can_find_kernel_file is not None
            assert has_modifed_testbench is not None
            assert has_modified_header is not None

            eval_data["can_find_kernel_file"] = can_find_kernel_file
            eval_data["has_modifed_testbench"] = has_modifed_testbench
            eval_data["has_modified_header"] = has_modified_header

            can_parse_output = (
                can_find_kernel_file is True
                and has_modifed_testbench is False
                and has_modified_header is False
            )
            eval_data["can_parse_output"] = can_parse_output
            if can_parse_output is False:
                serialize_eval_data(eval_id, eval_dir, eval_data)
                continue

            # make a design_generated dir
            design_generated_dir = eval_dir / "design_generated"
            design_generated_dir.mkdir()

            # copy the design files
            shutil.copy(design_header, design_generated_dir)
            shutil.copy(design_tb, design_generated_dir)
            shutil.copy(design_description, design_generated_dir)

            # copy the kernel file to the design_generated dir
            shutil.copy(fp_kernel_in_agent_run_dir, design_generated_dir)

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
