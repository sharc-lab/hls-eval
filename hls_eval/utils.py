import json
import time
from pathlib import Path
from typing import TypeVar

T = TypeVar("T")


def unwrap(value: T | None, error_message: str | None = None) -> T:
    if value is None:
        if error_message is None:
            raise ValueError("Unwrapped a None value")
        else:
            raise ValueError(error_message)
    return value


def check_key(key: str | None) -> str:
    if not key:
        raise ValueError("API key not found in .env file")
    else:
        return key


def load_jsonl_file(file_path: Path) -> list[dict]:
    txt = file_path.read_text()
    lines = txt.splitlines()
    return [json.loads(line) for line in lines]


def load_jsonl_text(txt: str) -> list[dict]:
    lines = txt.splitlines()
    return [json.loads(line) for line in lines]


class Timer:
    def __init__(self) -> None:
        self.start_time: None | float = None
        self.end_time: None | float = None
        self.time_taken: None | float = None

    def __enter__(self):
        self.start()
        return self

    def start(self) -> float:
        self.start_time = time.monotonic()
        assert self.start_time is not None
        return self.start_time

    def end(self) -> tuple[float, float, float]:
        self.end_time = time.monotonic()
        assert self.start_time is not None
        assert self.end_time is not None
        self.time_taken = self.end_time - self.start_time
        return self.start_time, self.end_time, self.time_taken

    def __exit__(self, exc_type, exc_value, traceback):
        self.end()
