import logging

import pytest
from vllm import SamplingParams

from hls_eval.llm import LLM_MODELS, build_model, destroy_model

logger = logging.getLogger(__name__)

models_to_keep = set([])
models_to_exclude = set(["deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"])
assert models_to_keep.isdisjoint(models_to_exclude)

LLM_MODELS_TO_TEST = LLM_MODELS
if len(models_to_keep) > 0:
    LLM_MODELS_TO_TEST = [m for m in LLM_MODELS if (m in models_to_keep)]
if len(models_to_exclude) > 0:
    LLM_MODELS_TO_TEST = [m for m in LLM_MODELS_TO_TEST if (m not in models_to_exclude)]

SEED = 7


@pytest.mark.parametrize("llm_name", LLM_MODELS_TO_TEST)
@pytest.mark.xdist_group(name="load_llms")
def test_load_models(llm_name: str):
    model = build_model(llm_name)
    assert model
    assert model.llm
    assert model.settings

    llm = model.llm

    sampling_params = SamplingParams(temperature=0.5, max_tokens=512, seed=SEED)
    conversation = [{"role": "user", "content": "What is the capital of France?"}]
    llm_output = llm.chat([conversation for _ in range(64)], sampling_params)  # type: ignore
    assert llm_output
    destroy_model(llm)
