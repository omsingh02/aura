from typing import Literal

LogLevel = Literal["INFO", "SUCCESS", "ERROR", "WARNING", "DEBUG"]


def log(message: str, level: LogLevel = "INFO") -> None:
    """Simple logger that only outputs ERROR level messages."""
    if level != "ERROR":
        return
    print(f"\033[91m{message}\033[0m")

