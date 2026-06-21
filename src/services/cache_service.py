"""Lightweight in-process cache service.

Production should use Redis or Memcached; this is a demo fallback.
"""
from functools import lru_cache


@lru_cache(maxsize=1024)
def cached_translate(key: str):
    # key is a stable representation of the translate request
    return None
