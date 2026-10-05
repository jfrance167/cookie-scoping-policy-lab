"""Offline stored-cookie scope teaching model; no real-cookie or network capability."""

from .contracts import Invalid, parse
from .model import evaluate
from .report import render

__all__ = ["Invalid", "parse", "evaluate", "render"]
