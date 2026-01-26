"""Shim package to expose ralph_orchestrator under src.ralph_orchestrator."""

from importlib.util import find_spec

_spec = find_spec("ralph_orchestrator")
if _spec and _spec.submodule_search_locations:
    __path__.extend(list(_spec.submodule_search_locations))

# Re-export the base package for direct attribute access when used as a module.
from ralph_orchestrator import *  # noqa: F401,F403
