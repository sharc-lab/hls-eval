import threading
import time
from collections import deque


class TokenBucket:
    def __init__(self, rate, capacity):
        self.rate = rate  # tokens per second
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = time.monotonic()
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        # For FIFO ordering
        self.next_ticket = 0  # Next ticket number to assign.
        self.waiting_queue = deque()  # Holds ticket numbers in order.

    def _refill(self):
        now = time.monotonic()
        time_passed = now - self.last_refill
        # Add tokens based on elapsed time, up to the bucket's capacity.
        self.tokens = min(self.capacity, self.tokens + time_passed * self.rate)
        self.last_refill = now

    def wait_for_token(self, tokens=1, verbose=False):
        """
        Block until the requested number of tokens are available.
        FIFO ordering is enforced: tasks are served in the order they call this method.
        """
        with self.condition:
            # Assign a ticket number for FIFO ordering.
            ticket = self.next_ticket
            self.next_ticket += 1
            self.waiting_queue.append(ticket)

            while True:
                # Wait until it's this task's turn.
                if self.waiting_queue[0] != ticket:
                    self.condition.wait()
                    continue

                # Refill tokens.
                self._refill()
                if verbose:
                    print(f"Tokens available: {self.tokens}, requested: {tokens}")

                # If enough tokens are available, consume them.
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    # Remove our ticket; it's now our turn.
                    self.waiting_queue.popleft()
                    self.condition.notify_all()  # Wake up any waiting threads.
                    return
                else:
                    # Wait a bit until more tokens accumulate.
                    self.condition.wait(timeout=0.1)


class MultiTokenBucket:
    def __init__(self, buckets):
        """
        buckets: List of tuples (rate, capacity) for each rate limit.
                 'rate' is tokens per second.
                 'capacity' is the maximum tokens that can accumulate.
        """
        self.buckets = []
        now = time.monotonic()
        for rate, capacity in buckets:
            self.buckets.append(
                {
                    "rate": rate,
                    "capacity": capacity,
                    "tokens": capacity,  # Start full.
                    "last_refill": now,
                }
            )
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        # For FIFO ordering: each waiting call gets a ticket number.
        self.next_ticket = 0
        self.waiting_queue = deque()  # Holds ticket numbers in submission order.

    def _refill(self):
        now = time.monotonic()
        for bucket in self.buckets:
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(
                bucket["capacity"], bucket["tokens"] + elapsed * bucket["rate"]
            )
            bucket["last_refill"] = now

    def wait_for(self, tokens_needed, verbose=False):
        """
        tokens_needed: List of token amounts to consume from each bucket.
                       The length should match the number of buckets.
        Blocks until tokens are available in all buckets and it's the task's turn.
        """
        if len(self.buckets) == 0:
            return
        with self.condition:
            # Assign a ticket for FIFO ordering.
            ticket = self.next_ticket
            self.next_ticket += 1
            self.waiting_queue.append(ticket)

            while True:
                # First, ensure it's this task's turn.
                if self.waiting_queue[0] != ticket:
                    # Not our turn yet; wait until notified.
                    self.condition.wait()
                    continue

                self._refill()
                # Check if all buckets have enough tokens.
                if all(
                    bucket["tokens"] >= needed
                    for bucket, needed in zip(self.buckets, tokens_needed)
                ):
                    # It's our turn and tokens are available. Reserve tokens.
                    for bucket, needed in zip(self.buckets, tokens_needed):
                        bucket["tokens"] -= needed
                    # Remove our ticket from the queue.
                    self.waiting_queue.popleft()
                    self.condition.notify_all()
                    return

                # Not enough tokens yet. Calculate wait time based on deficits.
                wait_times = []
                for bucket, needed in zip(self.buckets, tokens_needed):
                    deficit = max(0, needed - bucket["tokens"])
                    wait_times.append(
                        deficit / bucket["rate"] if bucket["rate"] else float("inf")
                    )
                wait_time = max(wait_times)
                self.condition.wait(timeout=wait_time)


class KeyedMultiTokenBucket:
    def __init__(self, buckets):
        """
        buckets: Dictionary where each key maps to a tuple (rate, capacity).
                 'rate' is tokens per second.
                 'capacity' is the maximum tokens that can accumulate.
        """
        self.buckets = {}
        now: float = time.monotonic()
        for key, (rate, capacity) in buckets.items():
            self.buckets[key] = {
                "rate": rate,
                "capacity": capacity,
                "tokens": capacity,  # Start full.
                "last_refill": now,
            }
        self.lock = threading.Lock()
        self.condition = threading.Condition(self.lock)
        # For FIFO ordering: each waiting call gets a ticket number.
        self.next_ticket = 0
        self.waiting_queue = deque()  # Holds ticket numbers in submission order.

    def _refill(self):
        now = time.monotonic()
        for bucket in self.buckets.values():
            elapsed = now - bucket["last_refill"]
            bucket["tokens"] = min(
                bucket["capacity"], bucket["tokens"] + elapsed * bucket["rate"]
            )
            bucket["last_refill"] = now

    def wait_for(self, **tokens_needed):
        """
        tokens_needed: Keyword arguments where each key corresponds to a bucket,
                       and the value is the number of tokens needed from that bucket.
        Blocks until tokens are available for all requested keys and it's the task's turn.
        """
        if len(self.buckets) == 0:
            return
        with self.condition:
            # Assign a ticket for FIFO ordering.
            ticket = self.next_ticket
            self.next_ticket += 1
            self.waiting_queue.append(ticket)

            while True:
                # Ensure it's this task's turn.
                if self.waiting_queue[0] != ticket:
                    self.condition.wait()
                    continue

                self._refill()

                # Check if all requested buckets have enough tokens.
                if all(
                    key in self.buckets and self.buckets[key]["tokens"] >= needed
                    for key, needed in tokens_needed.items()
                ):
                    # Reserve tokens from each bucket.
                    for key, needed in tokens_needed.items():
                        self.buckets[key]["tokens"] -= needed
                    # Remove our ticket from the queue and notify waiting threads.
                    self.waiting_queue.popleft()
                    self.condition.notify_all()
                    return

                # Not enough tokens yet. Calculate wait times based on deficits.
                wait_times = []
                for key, needed in tokens_needed.items():
                    if key not in self.buckets:
                        raise KeyError(f"Bucket key '{key}' not found.")
                    bucket = self.buckets[key]
                    deficit = max(0, needed - bucket["tokens"])
                    # Avoid division by zero if rate is 0.
                    wait_times.append(
                        deficit / bucket["rate"] if bucket["rate"] else float("inf")
                    )
                wait_time = max(wait_times)
                self.condition.wait(timeout=wait_time)


class RemoteLLMRateLimit:
    def __init__(
        self,
        requests_per_minute: int | None = None,
        tokens_per_minute: int | None = None,
    ):
        self.requests_per_minute = requests_per_minute
        self.tokens_per_minute = tokens_per_minute

        if self.requests_per_minute is None and self.tokens_per_minute is None:
            self.limiter = None
        elif self.requests_per_minute and not self.tokens_per_minute:
            self.limiter = KeyedMultiTokenBucket(
                {
                    "bucket_requests": (
                        self.requests_per_minute / 60,
                        self.requests_per_minute / 60,
                    )
                }
            )
        elif not self.requests_per_minute and self.tokens_per_minute:
            self.limiter = KeyedMultiTokenBucket(
                {
                    "bucket_tokens": (
                        self.tokens_per_minute / 60,
                        self.tokens_per_minute / 60,
                    )
                }
            )
        elif self.requests_per_minute and self.tokens_per_minute:
            self.limiter = KeyedMultiTokenBucket(
                {
                    "bucket_requests": (
                        self.requests_per_minute / 60,
                        self.requests_per_minute / 60,
                    ),
                    "bucket_tokens": (
                        self.tokens_per_minute / 60,
                        self.tokens_per_minute / 60,
                    ),
                }
            )
        else:
            raise ValueError("Unexpected configuration")

    def wait_for(self, tokens_needed: int):
        if not self.limiter:
            return
        else:
            request = {}
            if self.requests_per_minute:
                request["bucket_requests"] = 1
            if self.tokens_per_minute:
                request["bucket_tokens"] = tokens_needed

            self.limiter.wait_for(**request)
