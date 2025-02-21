import logging

import pytest
from dotenv import dotenv_values

from hls_eval.llm import build_model_remote_tai
from hls_eval.utils import check_key

API_KEY_TOGETHERAI = check_key(dotenv_values(".env")["TOGETHER_API_KEY"])

LOGGER = logging.getLogger(__name__)

models_to_keep = set([])
models_to_exclude = set(["deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct"])
assert models_to_keep.isdisjoint(models_to_exclude)

# LLM_MODELS_TO_TEST = LLM_MODELS
# if len(models_to_keep) > 0:
#     LLM_MODELS_TO_TEST = [m for m in LLM_MODELS if (m in models_to_keep)]
# if len(models_to_exclude) > 0:
#     LLM_MODELS_TO_TEST = [m for m in LLM_MODELS_TO_TEST if (m not in models_to_exclude)]


MODELS_TO_TEST_REMOTE = [
    "Qwen/Qwen2.5-Coder-32B-Instruct",
    # "google/gemma-2-27b-it",
    "meta-llama/Llama-3-70b-chat-hf",
    "meta-llama/Llama-3-8b-chat-hf",
]


SEED = 7


# @pytest.mark.parametrize("llm_name", LLM_MODELS_TO_TEST)
# @pytest.mark.xdist_group(name="load_llms")
# def test_load_models(llm_name: str):
#     model = build_model(llm_name)
#     assert model
#     assert model.llm
#     assert model.settings

#     llm = model.llm

#     sampling_params = SamplingParams(temperature=0.5, max_tokens=512, seed=SEED)
#     conversation = [{"role": "user", "content": "What is the capital of France?"}]
#     llm_output = llm.chat([conversation for _ in range(64)], sampling_params)  # type: ignore
#     assert llm_output
#     destroy_model(llm)


@pytest.mark.parametrize("llm_name", MODELS_TO_TEST_REMOTE)
@pytest.mark.xdist_group(name="load_llms")
def test_run_remote_models(llm_name: str):
    LOGGER.info(f"Testing model: {llm_name}")
    model = build_model_remote_tai(llm_name, API_KEY_TOGETHERAI)
    llm = model.llm
    response = llm.prompt(
        "What is the capital of France?", temperature=0.5, stream=False
    )
    txt = response.text()
    assert "paris" in txt.lower()


@pytest.mark.parametrize("llm_name", MODELS_TO_TEST_REMOTE)
@pytest.mark.xdist_group(name="load_llms")
def test_run_remote_models_conversation(llm_name: str):
    LOGGER.info(f"Testing model: {llm_name}")
    model = build_model_remote_tai(llm_name, API_KEY_TOGETHERAI)
    llm = model.llm
    conversation = llm.conversation()

    response = conversation.prompt(
        "What is the capital of France?", temperature=0.5, stream=False
    )
    txt = response.text()
    LOGGER.info(f"Response: {txt}")
    assert "paris" in txt.lower()

    response = conversation.prompt(
        "What country is that capital in?", temperature=0.5, stream=False
    )
    txt = response.text()
    LOGGER.info(f"Response: {txt}")
    assert "france" in txt.lower()
