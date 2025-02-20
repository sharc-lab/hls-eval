import logging
from functools import partial
from pathlib import Path

from hls_eval.llm import build_model

EXP_NAME = "hls_gen_zero_shot"

DIR_CURRENT = Path(__file__).resolve().parent
DIR_ROOT = DIR_CURRENT.parent.parent
DIR_HLS_EVAL_DATA = DIR_ROOT / "hls_eval_data"

LOGGER = logging.getLogger(EXP_NAME)
LOGGER.propagate = True
LOGGER.setLevel(logging.DEBUG)


if __name__ == "__main__":
    model_to_test = "Qwen/Qwen2.5-Coder-3B-Instruct"
    model_to_test_builder = partial(build_model, model_name=model_to_test)

    # make prompts
    # make eval parallel pools
    # make eval repo

    # run eval

    # zip results
