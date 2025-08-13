# app/utils/helpers.py

import textwrap
import datetime


def dedent_and_strip(text: str) -> str:
    """
    Cleans up multiline strings by removing indentation and stripping.
    """
    return textwrap.dedent(text).strip()


def format_timestamp(ts: float = None) -> str:
    """
    Format a UNIX timestamp or current time as human-readable string.
    """
    dt = datetime.datetime.fromtimestamp(ts or datetime.datetime.now().timestamp())
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def safe_get(d: dict, key: str, default=None):
    """
    Safe dict access with fallback value.
    """
    return d.get(key, default)
