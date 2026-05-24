import json
import os
import shlex
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import docker
from docker.models.containers import Container
from llm_openrouter import OpenRouterChat

from hls_eval.data import BenchmarkCase
from hls_eval.eval import EvalThreadPools, Evaluator, serialize_eval_data
from hls_eval.llms import Model, normalize_model_name
from hls_eval.prompts import build_prompt_gen_agentic
from hls_eval.tools import VitisHLSCSimTool, VitisHLSSynthTool
from hls_eval.utils import load_jsonl_text

DOCKER_IMAGE_NAME = "hls-eval-agent-pi"
CONTAINER_WORKDIR = "/workspace"

LIMIT_KEYWORDS = (
    "limit exceeded",
    "rate limit",
    "quota exceeded",
    "too many requests",
    "429",
)


@dataclass
class PiAgentRunResult:
    exit_code: int
    output: str
    agent_submitted: bool
    agent_limit_exceeded: bool
    agent_trace: list[dict[str, Any]]
    session_file: Path | None
    session_html_file: Path | None


def setup_pi_config(agent_run_dir: Path, model_name: str) -> Path:
    dir_pi_config = agent_run_dir / ".pi"
    dir_sessions = dir_pi_config / "sessions"
    dir_pi_config.mkdir(parents=True, exist_ok=True)
    dir_sessions.mkdir(parents=True, exist_ok=True)

    pi_settings = {
        "defaultProvider": "openrouter",
        "defaultModel": model_name,
        "sessionDir": ".pi/sessions",
    }
    (dir_pi_config / "settings.json").write_text(json.dumps(pi_settings, indent=4))

    os.chmod(dir_pi_config, 0o777)
    os.chmod(dir_sessions, 0o777)
    return dir_pi_config


def _detect_limit_exceeded(exit_code: int, output: str) -> bool:
    if exit_code == 0:
        return False
    output_lower = output.lower()
    return any(keyword in output_lower for keyword in LIMIT_KEYWORDS)


def run_pi_agent(
    agent_run_dir: Path,
    prompt: str,
    model_name: str,
    api_key: str,
    docker_image_name: str = DOCKER_IMAGE_NAME,
) -> PiAgentRunResult:
    setup_pi_config(agent_run_dir, model_name)

    # check that the docker image exists
    client = docker.from_env()
    try:
        client.images.get(docker_image_name)
    except docker.errors.ImageNotFound:
        raise RuntimeError(f"Docker image {docker_image_name} not found")

    container: Container | None = None
    try:
        container = client.containers.run(
            image=docker_image_name,
            command="sleep 2h",
            detach=True,
            volumes={
                str(agent_run_dir.resolve()): {
                    "bind": CONTAINER_WORKDIR,
                    "mode": "rw",
                }
            },
        )

        quoted_prompt = shlex.quote(prompt)
        exit_code, output_bytes = container.exec_run(
            ["sh", "-lc", f"umask 000 && pi -p {quoted_prompt}"],
            environment={"OPENROUTER_API_KEY": api_key},
            workdir=CONTAINER_WORKDIR,
        )
        output = (
            output_bytes.decode("utf-8")
            if isinstance(output_bytes, bytes)
            else str(output_bytes)
        )

        dir_sessions = agent_run_dir / ".pi" / "sessions"
        session_file = next(dir_sessions.glob("*.jsonl"), None)
        agent_trace: list[dict[str, Any]] = []
        session_html_file: Path | None = None

        if session_file is not None:
            agent_trace = load_jsonl_text(session_file.read_text())
            session_html_file = session_file.with_suffix(".html")
            export_cmd = (
                "umask 000 && pi --export "
                f"/workspace/.pi/sessions/{session_file.name} "
                f"/workspace/.pi/sessions/{session_html_file.name}"
            )
            export_exit_code, export_output = container.exec_run(
                ["sh", "-lc", export_cmd],
                workdir=CONTAINER_WORKDIR,
            )
            if export_exit_code != 0:
                export_text = (
                    export_output.decode("utf-8")
                    if isinstance(export_output, bytes)
                    else str(export_output)
                )
                raise RuntimeError(
                    f"Failed to export Pi session to HTML: {export_text}"
                )

        agent_submitted = exit_code == 0
        agent_limit_exceeded = _detect_limit_exceeded(exit_code, output)

        return PiAgentRunResult(
            exit_code=exit_code,
            output=output,
            agent_submitted=agent_submitted,
            agent_limit_exceeded=agent_limit_exceeded,
            agent_trace=agent_trace,
            session_file=session_file,
            session_html_file=session_html_file,
        )
    finally:
        if container is not None:
            container.stop()
            container.remove(force=True)


class HLSGenerationAgentEvaluatorPi(Evaluator):
    def __init__(
        self,
        vitis_hls_tool_csim: VitisHLSCSimTool,
        vitis_hls_tool_synth: VitisHLSSynthTool,
        output_data_dir: Path,
        n_samples: int = 1,
        temperature: float = 0.7,
        docker_image_name: str = DOCKER_IMAGE_NAME,
    ) -> None:
        self.n_samples = n_samples
        self.temperature = temperature
        self.docker_image_name = docker_image_name

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

            eval_data["eval_type"] = "hls_gen_agentic_pi"
            eval_data["eval_id"] = eval_id
            eval_data["benchmark_case_name"] = benchmark_case_name
            eval_data["benchmark_case_tags"] = benchmark_case.tags_all
            eval_data["model_name"] = model_name
            eval_data["model_name_normalized"] = model_name_normalized
            eval_data["docker_image_name"] = self.docker_image_name

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
            design_tb_data_files = benchmark_case.tb_data_files

            agent_run_dir = eval_dir / "agent_run_dir"
            agent_run_dir.mkdir()

            shutil.copy(design_description, agent_run_dir)
            shutil.copy(design_header, agent_run_dir)
            shutil.copy(design_tb, agent_run_dir)
            for tb_data_file in design_tb_data_files:
                shutil.copy(tb_data_file, agent_run_dir)

            prompt = build_prompt_gen_agentic(
                fn_design_description=design_description.name,
                fn_design_h=design_header.name,
                fn_design_tb=design_tb.name,
                fn_design_kernel=design_kernel.name,
            )
            eval_data["prompt"] = prompt
            (eval_dir / "raw_agent_prompt.txt").write_text(prompt)

            if isinstance(model.llm, OpenRouterChat):
                copy_model_name = model.llm.model_name
                copy_api_key = model.llm.key
                if copy_api_key is None:
                    raise ValueError(f"API key not found for model {model_name}")
            else:
                raise NotImplementedError(
                    f"Model {model_name} is not an OpenRouter model, only OpenRouter models are supported for agent evals right now."
                )

            def run_agent_attempt() -> tuple[
                PiAgentRunResult,
                float,
                float,
                float,
            ]:
                t0 = time.monotonic()
                result = run_pi_agent(
                    agent_run_dir=agent_run_dir,
                    prompt=prompt,
                    model_name=copy_model_name,
                    api_key=copy_api_key,
                    docker_image_name=self.docker_image_name,
                )
                t1 = time.monotonic()
                dt = t1 - t0
                return result, t0, t1, dt

            pool_agent = pools.pool_agent
            future_agent = pool_agent.submit(run_agent_attempt)
            pi_result, t0, t1, dt = future_agent.result()

            eval_data["agent_execution_time"] = {
                "t0": t0,
                "t1": t1,
                "execution_time": dt,
            }
            eval_data["agent_submitted"] = pi_result.agent_submitted
            eval_data["agent_limit_exceeded"] = pi_result.agent_limit_exceeded
            eval_data["agent_exit_code"] = pi_result.exit_code
            eval_data["agent_output"] = pi_result.output
            eval_data["agent_trace"] = pi_result.agent_trace

            (eval_dir / "agent_output.txt").write_text(pi_result.output)
            (eval_dir / "trace.json").write_text(
                json.dumps(pi_result.agent_trace, indent=4)
            )

            if pi_result.session_file is not None:
                shutil.copy(
                    pi_result.session_file,
                    eval_dir / pi_result.session_file.name,
                )
            if (
                pi_result.session_html_file is not None
                and pi_result.session_html_file.exists()
            ):
                shutil.copy(
                    pi_result.session_html_file,
                    eval_dir / "trace.html",
                )

            if pi_result.agent_limit_exceeded is True:
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

            design_generated_dir = eval_dir / "design_generated"
            design_generated_dir.mkdir()

            shutil.copy(design_header, design_generated_dir)
            shutil.copy(design_tb, design_generated_dir)
            shutil.copy(design_description, design_generated_dir)
            for tb_data_file in design_tb_data_files:
                shutil.copy(tb_data_file, design_generated_dir)

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
