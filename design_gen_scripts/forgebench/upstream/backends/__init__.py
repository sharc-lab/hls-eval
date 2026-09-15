"""Tool backends for the ForgeBench generators.

The four `<domain>/generate_code.py` files are copy-paste forks that are run with
the domain directory as cwd, so `import backends` does not resolve on its own.
Each generator puts the repo root on `sys.path` first:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    import backends

Emission sites deep inside the generators (loop openings, partition pragmas) are
numerous and would need a `backend` argument threaded through ~20 helper
functions. Instead the active backend is process-global state, set once per design
by `gen_configs.run_hls_flow`. `run_hls_configs.py` fans designs out across
separate processes (`ProcessPoolExecutor`), so there is no sharing hazard.
"""
from backends.base import ToolBackend, effective_pragma_factor, get_backend, normalize_data_type
from backends import catapult as _catapult  # noqa: F401  (registers the backend)
from backends import vitis as _vitis  # noqa: F401  (registers the backend)

_current = None


def set_current(name):
    """Select the backend for subsequent generation. Returns the instance."""
    global _current
    _current = get_backend(name)
    return _current


def current():
    """The active backend, defaulting to Vitis for backward compatibility."""
    global _current
    if _current is None:
        _current = get_backend("vitis")
    return _current


__all__ = [
    "ToolBackend",
    "current",
    "effective_pragma_factor",
    "get_backend",
    "normalize_data_type",
    "set_current",
]
