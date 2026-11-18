"""Translations. API data stays in canonical English; these files localise it.

Each <lang>.yaml has:
  ui:    interface strings (keyed)
  terms: canonical English term -> localised term (grahas, rashis, nakshatras, ...)
  abbr:  short planet labels for chart drawings
  rules: rule id -> {name, text} for the rules engine
"""
from __future__ import annotations

import functools
import pathlib

import yaml

DIR = pathlib.Path(__file__).parent
LANGS = ("en", "hi")


@functools.lru_cache(maxsize=None)
def load(lang: str) -> dict:
    if lang not in LANGS:
        raise ValueError(f"unsupported language '{lang}'")
    data = yaml.safe_load((DIR / f"{lang}.yaml").read_text(encoding="utf-8")) or {}
    for k in ("ui", "terms", "abbr", "rules"):
        data.setdefault(k, {})
    return data


def term(lang: str, value: str) -> str:
    return load(lang)["terms"].get(value, value) if lang != "en" else value
