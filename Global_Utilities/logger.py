from __future__ import annotations

import sys
from typing import NoReturn

RESET = "\033[0m"
BLUE = "\033[94m"
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"


def _log(color: str, tag: str, symbol: str, message: str) -> None:
    print(f"{color}{tag} {symbol} {message}{RESET}")


def info(message: str) -> None:
    _log(BLUE, "[INFO]", "?", message)


def warn(message: str) -> None:
    _log(YELLOW, "[WARN]", "!", message)


def success(message: str) -> None:
    _log(GREEN, "[SUCCESS]", ":)", message)


def error(message: str) -> NoReturn:
    _log(RED, "[ERROR]", "!!!", message)
    sys.exit(1)
