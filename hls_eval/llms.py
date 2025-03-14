# os.environ["VLLM_USE_V1"] = "1"
import time
from dataclasses import dataclass, field
from typing import Any

import llm
import requests
from pydantic import Field

# from vllm import (
#     AsyncEngineArgs,
#     AsyncLLMEngine,
#     SamplingParams,
#     TextPrompt,
#     TokensPrompt,
# )
# from vllm.config import ModelConfig
# from vllm.distributed.parallel_state import (
#     destroy_distributed_environment,
#     destroy_model_parallel,
# )
# from vllm.entrypoints.chat_utils import (
#     ChatCompletionMessageParam,
#     ChatTemplateContentFormatOption,
#     apply_hf_chat_template,
#     apply_mistral_chat_template,
#     parse_chat_messages,
#     resolve_chat_template_content_format,
# )
# from vllm.outputs import RequestOutput
# from vllm.transformers_utils.tokenizers.mistral import MistralTokenizer

# COMMON_VLLM_ARGS = {
#     "tensor_parallel_size": 2,
#     "gpu_memory_utilization": 0.9,
#     "trust_remote_code": True,
#     "distributed_executor_backend": "mp",
#     "enable_lora": False,
#     "enforce_eager": False,
#     "enable_prefix_caching": True,
#     "compilation_config": 3,
#     "enable_chunked_prefill": True,
#     "disable_custom_all_reduce": True,
#     # "block_size": 32,
#     "max_model_len": 8192,
#     "max_seq_len_to_capture": 8192,
#     "max_num_batched_tokens": 8192,
#     "max_num_seqs": 128,
#     "seed": 0,
# }


# LLM_MODELS = [
#     "Qwen/Qwen2.5-Coder-1.5B-Instruct",
#     "Qwen/Qwen2.5-Coder-3B-Instruct",
#     "Qwen/Qwen2.5-Coder-7B-Instruct",
#     # "deepseek-ai/DeepSeek-Coder-V2-Lite-Instruct",
#     "google/gemma-2-2b-it",
#     "google/gemma-2-9b-it",
#     "google/codegemma-7b-it",
#     "meta-llama/Llama-3.2-1B-Instruct",
#     "meta-llama/Llama-3.2-3B-Instruct",
# ]


# class ReuqestCounter:
#     def __init__(self, start: int = 0) -> None:
#         self.counter = start
#         self.mutex = Lock()

#     def __next__(self) -> int:
#         with self.mutex:
#             i = self.counter
#             self.counter += 1
#         return i

#     def reset(self) -> None:
#         with self.mutex:
#             self.counter = 0


# @dataclass
# class ModelLocalvLLM:
#     name: str
#     llm_async_engine: AsyncLLMEngine
#     settings: dict[str, bool | int | str | float] = field(default_factory=dict)
#     other: dict[str, Any] = field(default_factory=dict)
#     llm_request_counter = ReuqestCounter()


# def build_model_local_vllm(model_name: str, **kwargs) -> ModelLocalvLLM:
#     llm_args = deepcopy(COMMON_VLLM_ARGS)
#     for k, v in kwargs.items():
#         llm_args[k] = v
#     llm_args["model"] = model_name
#     engine_args = AsyncEngineArgs(**llm_args)
#     engine = AsyncLLMEngine.from_engine_args(engine_args)
#     return ModelLocalvLLM(name=model_name, llm_async_engine=engine, settings=llm_args)


# def destroy_model_local_vllm(model: ModelLocalvLLM) -> None:
#     model.llm_async_engine.shutdown_background_loop()
#     del model.llm_async_engine
#     del model
#     destroy_model_parallel()
#     destroy_distributed_environment()

#     gc.collect()
#     torch.cuda.empty_cache()


# def is_list_of(obj: Any, type_: type) -> bool:
#     return isinstance(obj, list) and all(isinstance(x, type_) for x in obj)


# def get_default_sampling_params(model_config: ModelConfig) -> SamplingParams:
#     diff_sampling_param = model_config.get_diff_sampling_param()
#     if diff_sampling_param:
#         return SamplingParams.from_optional(**diff_sampling_param)
#     return SamplingParams()


# async def gen_wrapper(
#     generator: AsyncGenerator[RequestOutput, None],
# ) -> list[RequestOutput]:
#     return [x async for x in generator]


# def chat(
#     model: ModelLocalvLLM,
#     messages: Union[
#         List[ChatCompletionMessageParam], List[List[ChatCompletionMessageParam]]
#     ],
#     sampling_params: Optional[Union[SamplingParams, List[SamplingParams]]] = None,
#     chat_template: Optional[str] = None,
#     chat_template_content_format: ChatTemplateContentFormatOption = "auto",
# ):
#     list_of_messages: List[List[ChatCompletionMessageParam]]

#     # Handle multi and single conversations
#     if is_list_of(messages, list):
#         # messages is List[List[...]]
#         list_of_messages = cast(List[List[ChatCompletionMessageParam]], messages)
#     else:
#         # messages is List[...]
#         list_of_messages = [cast(List[ChatCompletionMessageParam], messages)]

#     tokenizer = asyncio.run(model.llm_async_engine.get_tokenizer())
#     model_config = asyncio.run(model.llm_async_engine.get_model_config())

#     resolved_content_format = resolve_chat_template_content_format(
#         chat_template,
#         chat_template_content_format,
#         tokenizer,
#     )

#     prompts: List[Union[TokensPrompt, TextPrompt]] = []

#     for msgs in list_of_messages:
#         # NOTE: _parse_chat_message_content_parts() currently doesn't
#         # handle mm_processor_kwargs, since there is no implementation in
#         # the chat message parsing for it.
#         conversation, mm_data = parse_chat_messages(
#             msgs,
#             model_config,
#             tokenizer,
#             content_format=resolved_content_format,
#         )

#         prompt_data: Union[str, List[int]]
#         if isinstance(tokenizer, MistralTokenizer):
#             prompt_data = apply_mistral_chat_template(
#                 tokenizer,
#                 messages=msgs,
#                 chat_template=chat_template,
#             )
#         else:
#             prompt_data = apply_hf_chat_template(
#                 tokenizer,
#                 conversation=conversation,
#                 chat_template=chat_template,
#             )

#         prompt: Union[TokensPrompt, TextPrompt]
#         if is_list_of(prompt_data, int):
#             assert isinstance(prompt_data, list)
#             prompt = TokensPrompt(prompt_token_ids=prompt_data)
#         else:
#             assert isinstance(prompt_data, str)
#             prompt = TextPrompt(prompt=prompt_data)

#         prompts.append(prompt)

#     all_sampling_params = None
#     if sampling_params is not None:
#         if is_list_of(sampling_params, SamplingParams):
#             assert isinstance(sampling_params, list)
#             assert len(sampling_params) == len(list_of_messages)
#             all_sampling_params = cast(List[SamplingParams], sampling_params)
#         else:
#             all_sampling_params = [cast(SamplingParams, sampling_params)]
#     else:
#         all_sampling_params = [get_default_sampling_params(model_config)]

#     co_generate_all: list[AsyncGenerator[RequestOutput, None]] = []

#     for p, s in zip(prompts, all_sampling_params):
#         request_id = str(next(model.llm_request_counter))
#         co_generate: AsyncGenerator[RequestOutput, None] = (
#             model.llm_async_engine.generate(
#                 request_id=request_id,
#                 prompt=p,
#                 sampling_params=s,
#             )
#         )
#         co_generate_all.append(co_generate)

#     outputs_gathered = asyncio.gather(
#         *[gen_wrapper(co_gen) for co_gen in co_generate_all]
#     )
#     output = outputs_gathered.result()

#     return output


@dataclass
class Model:
    name: str
    llm: llm.Model
    settings: dict[str, bool | int | str | float] = field(default_factory=dict)
    other: dict[str, Any] = field(default_factory=dict)


class TAITimeout(Exception): ...


class TAIPromptTooLong(Exception): ...


class TogetherAI(llm.Model):
    needs_key = "togetherai"
    key_env_var = "TOGETHER_API_KEY"

    class Options(llm.Options):  # type: ignore
        max_tokens: int | None = Field(
            ge=1,
            default=None,
        )
        stop: list[str] | None = Field(
            default=["<|eot_id|>", "</s>", "[INST]"],
        )
        temperature: float | None = Field(
            ge=0,
            default=None,
        )
        top_p: float | None = Field(
            ge=0,
            default=None,
        )
        top_k: int | None = Field(
            ge=0,
            default=None,
        )
        repetition_penalty: float | None = Field(
            ge=0,
            default=None,
        )
        json_schema_output: dict[str, Any] | None = Field(
            default=None,
        )

    API_URL_INFERENCE = "https://api.together.xyz/v1/chat/completions"

    def __init__(self, model_id, model_id_tai):
        self.model_id = model_id
        self.model_id_tai = model_id_tai

    def execute(
        self,
        prompt: llm.Prompt,
        stream: bool,
        response: llm.Response,
        conversation: llm.Conversation | None,
    ):
        assert prompt.options
        assert isinstance(prompt.options, self.Options)

        if stream:
            raise NotImplementedError("streaming not supported")

        payload: dict[str, Any] = {}

        payload["model"] = self.model_id_tai

        payload["messages"] = []
        if prompt.system:
            payload["messages"].append({"role": "system", "content": prompt.system})

        if conversation:
            for r in conversation.responses:
                payload["messages"].append({"role": "user", "content": r.prompt.prompt})
                payload["messages"].append(
                    {"role": "assistant", "content": r.text()}  # type: ignore
                )

        payload["messages"].append({"role": "user", "content": prompt.prompt})

        if prompt.options.json_schema_output:
            payload["response_format"] = {}
            payload["response_format"]["type"] = "json_object"
            payload["response_format"]["schema"] = prompt.options.json_schema_output

        if prompt.options.stop:
            payload["stop"] = prompt.options.stop

        if prompt.options.max_tokens:
            payload["max_tokens"] = prompt.options.max_tokens

        headers = {
            "accept": "application/json",
            "content-type": "application/json",
            "Authorization": f"Bearer {self.key}",
        }

        r = requests.post(self.API_URL_INFERENCE, json=payload, headers=headers)
        status_code = r.status_code
        if status_code == 524:
            raise TAITimeout("Model took too long to respond on TogetherAI's side")
        if status_code == 422:
            raise TAIPromptTooLong("Prompt too long for model max prompt size")

        codes_to_retry = {520, 502, 503, 500}

        if status_code in codes_to_retry:
            print(f"Error on inital request: {status_code}")
            # try again 5 times if status code is still broken
            i = 0
            while i < 5 and status_code in codes_to_retry:
                time.sleep(5)
                print(f"Erorr logged in retry loop: {status_code}")
                print(f"Retrying {i + 1}/5")
                r = requests.post(self.API_URL_INFERENCE, json=payload, headers=headers)
                status_code = r.status_code
                if status_code == 524:
                    raise TAITimeout(
                        "Model took too long to respond on TogetherAI's side"
                    )
                if status_code not in codes_to_retry:
                    break
                i += 1

        try:
            r.raise_for_status()
        except requests.HTTPError as e:
            print(e)
            print(r.text)
            raise e
        data = r.json()

        response.response_json = data  # type: ignore

        assert data["choices"]
        assert len(data["choices"]) > 0
        first_choice = data["choices"][0]
        assert first_choice["message"]
        assert first_choice["message"]["role"] == "assistant"
        assert first_choice["message"]["content"]
        return first_choice["message"]["content"]


TModelSettings = dict[str, Any]


def build_model_remote_tai(
    model_name: str, api_key: str | None = None, **kwargs
) -> Model:
    model = TogetherAI(model_name, model_name)
    model.key = api_key
    if "settings" in kwargs:
        settings = kwargs["settings"]
    else:
        settings = {}
    return Model(name=model_name, llm=model, settings=settings)


class vLLMModel(llm.Model):
    # needs_key = "togetherai"
    # key_env_var = "TOGETHER_API_KEY"

    class Options(llm.Options):  # type: ignore
        max_tokens: int | None = Field(
            ge=1,
            default=None,
        )
        stop: list[str] | None = Field(
            default=["<|eot_id|>", "</s>", "[INST]"],
        )
        temperature: float | None = Field(
            ge=0,
            default=None,
        )
        top_p: float | None = Field(
            ge=0,
            default=None,
        )
        top_k: int | None = Field(
            ge=0,
            default=None,
        )
        repetition_penalty: float | None = Field(
            ge=0,
            default=None,
        )
        json_schema_output: dict[str, Any] | None = Field(
            default=None,
        )

    def __init__(self, model_id, model_id_hf):
        self.model_id = model_id
        self.model_id_hf = model_id_hf

        # TODO: implement rest of local inference
        # slef.vllm_llm = LLM(model_id_hf)
        raise NotImplementedError

    def execute(
        self,
        prompt: llm.Prompt,
        stream: bool,
        response: llm.Response,
        conversation: llm.Conversation | None,
    ):
        assert prompt.options
        assert isinstance(prompt.options, self.Options)

        if stream:
            raise NotImplementedError("streaming not supported")

        # TODO: implement rest of lcoal infernece
        raise NotImplementedError


def normalize_model_name(model_name: str) -> str:
    return model_name.replace("/", "_").replace("-", "_").replace(" ", "_").lower()
