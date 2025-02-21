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
