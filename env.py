import os
import ast
from typing import Any
from dotenv import load_dotenv as _load_dotenv


def __getattr__(name: str) -> Any:
    val = os.getenv(name)
    try:
        return ast.literal_eval(val)
    except ValueError:
        return val


def load_dotenv(*args, **kwargs):
    return _load_dotenv(*args, **kwargs)
