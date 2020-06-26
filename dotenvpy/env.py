import os
import ast

from typing import Any


def __getattr__(name: str) -> Any:
    val = os.getenv(name)
    try:
        return ast.literal_eval(val)
    except:
        return val
