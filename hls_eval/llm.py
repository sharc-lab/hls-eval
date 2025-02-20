import os
from dataclasses import dataclass, field
from typing import Any

os.environ["VLLM_USE_V1"] = "1"

import gc
from copy import deepcopy

import torch
from vllm import LLM
from vllm.distributed.parallel_state import (
    destroy_distributed_environment,
    destroy_model_parallel,
)

COMMON_VLLM_ARGS = {
    "tensor_parallel_size": 2,
    "gpu_memory_utilization": 0.9,
    "trust_remote_code": True,
    "distributed_executor_backend": "mp",
    "enable_lora": False,
    "enforce_eager": False,
    "enable_prefix_caching": True,
    "compilation_config": 3,
    "enable_chunked_prefill": True,
    "disable_custom_all_reduce": True,
    "block_size": 32,
    "max_model_len": 8192,
    "max_seq_len_to_capture": 8192,
    "max_num_batched_tokens": 8192,
    "max_num_seqs": 128,
    "seed": 0,
}


LLM_MODELS = [
    "Qwen/Qwen2.5-Coder-1.5B-Instruct",
    "Qwen/Qwen2.5-Coder-3B-Instruct",
    "Qwen/Qwen2.5-Coder-7B-Instruct",
    # "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
    "google/gemma-2-2b-it",
    "google/gemma-2-9b-it",
    "google/codegemma-7b-it",
    "meta-llama/Llama-3.2-1B-Instruct",
    "meta-llama/Llama-3.2-3B-Instruct",
]


@dataclass
class Model:
    name: str
    llm: LLM
    settings: dict[str, bool | int | str | float] = field(default_factory=dict)
    other: dict[str, Any] = field(default_factory=dict)


def build_model(model_name: str, **kwargs) -> Model:
    llm_params = deepcopy(COMMON_VLLM_ARGS)
    for k, v in kwargs.items():
        llm_params[k] = v
    llm = LLM(model_name, **llm_params)
    return Model(name=model_name, llm=llm, settings=llm_params)


def destroy_model(llm: LLM) -> None:
    del llm.llm_engine
    del llm
    destroy_model_parallel()
    destroy_distributed_environment()

    gc.collect()
    torch.cuda.empty_cache()
