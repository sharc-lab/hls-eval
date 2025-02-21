import logging
import time
from concurrent.futures import ThreadPoolExecutor

from hls_eval.rate_limit import KeyedMultiTokenBucket, MultiTokenBucket, TokenBucket

LOGGER = logging.getLogger(__name__)


def test_token_bucket():
    def task(token_bucket: TokenBucket, task_id: int) -> None:
        token_bucket.wait_for_token(1)
        LOGGER.info(f"Task {task_id} started at {time.strftime('%X')}")
        time.sleep(1)
        LOGGER.info(f"Task {task_id} finished at {time.strftime('%X')}")

    rate = 2
    capacity = 2
    token_bucket = TokenBucket(rate, capacity)

    with ThreadPoolExecutor(max_workers=5) as executor:
        for i in range(5):
            executor.submit(task, token_bucket, i)


def test_multi_token_bucket():
    buckets = [
        (4, 4),
        (3, 3),
    ]

    limiter = MultiTokenBucket(buckets)

    def task(limiter: MultiTokenBucket, tokens_needed: list[int], task_id: str) -> None:
        LOGGER.info(
            f"Task {task_id} waiting for tokens {tokens_needed} at {time.strftime('%X')}"
        )
        limiter.wait_for(tokens_needed)
        LOGGER.info(f"Task {task_id} started at {time.strftime('%X')}")
        time.sleep(1)
        LOGGER.info(f"Task {task_id} finished at {time.strftime('%X')}")

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(task, limiter, [2, 3], "A")
        executor.submit(task, limiter, [4, 1], "B")
        executor.submit(task, limiter, [1, 1], "C")


def test_keyed_multi_token_bucket():
    # Define two keyed buckets: each key maps to a tuple (rate, capacity).
    buckets_config = {
        "bucket1": (4, 4),  # 4 tokens per second with capacity 4.
        "bucket2": (3, 3),  # 3 tokens per second with capacity 3.
    }

    limiter = KeyedMultiTokenBucket(buckets_config)

    def task(
        limiter: KeyedMultiTokenBucket, tokens_needed: dict[str, int], task_id: str
    ) -> None:
        LOGGER.info(
            f"Task {task_id} waiting for tokens {tokens_needed} at {time.strftime('%X')}"
        )
        # Pass token requirements via keyword arguments.
        limiter.wait_for(**tokens_needed)
        LOGGER.info(f"Task {task_id} started at {time.strftime('%X')}")
        time.sleep(1)  # Simulate task duration.
        LOGGER.info(f"Task {task_id} finished at {time.strftime('%X')}")

    # Use ThreadPoolExecutor to run tasks concurrently.
    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.submit(task, limiter, {"bucket1": 2, "bucket2": 3}, "A")
        executor.submit(task, limiter, {"bucket1": 4, "bucket2": 1}, "B")
        executor.submit(task, limiter, {"bucket1": 1, "bucket2": 1}, "C")
