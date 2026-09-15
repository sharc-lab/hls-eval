"""Tool-backend abstraction for the ForgeBench generators (review concern E1).

Every generated design used to be Vitis-specific in four places: the `ap_fixed`
types, the `#pragma HLS ...` directives, the `m_axi` interface pragmas, and
`run_hls.tcl`. A `ToolBackend` owns all four, so the same JSON config can emit a
Vitis project or a Catapult project.

Registry style mirrors `analysis/extractors/base.py` so both halves of the repo
select a tool the same way.

Note on loop emission: Vitis puts `#pragma HLS unroll factor=N` *inside* the loop
body; Catapult wants `#pragma hls_unroll N` *immediately before* the `for`. A hook
that only returns a pragma string cannot express that difference, which is why the
backend owns `open_loop()` — the whole loop opening — rather than just the pragma.
"""
import re

_REGISTRY = {}


def register(cls):
    _REGISTRY[cls.name] = cls
    return cls


def get_backend(name):
    if name not in _REGISTRY:
        raise ValueError(
            f"unknown tool backend {name!r}; available: {sorted(_REGISTRY)}"
        )
    return _REGISTRY[name]()


# --------------------------------------------------------------------------
# Data types
# --------------------------------------------------------------------------

_FIXED_RE = re.compile(r"^\s*(?:ap_|ac_)?fixed\s*<\s*(\d+)\s*,\s*(-?\d+)\s*(?:,[^>]*)?>\s*$")


def normalize_data_type(data_type):
    """Canonicalize a config `data_type` into a tool-neutral form.

    Accepts the legacy Vitis spellings (`ap_fixed<16, 5>` — what all 3840 gemm
    configs currently contain), the Catapult spelling, the neutral spelling, and
    plain scalars. Returns ``("fixed", W, I)`` or ``("scalar", name, None)``.
    """
    dt = data_type.strip()
    m = _FIXED_RE.match(dt)
    if m:
        return ("fixed", int(m.group(1)), int(m.group(2)))
    return ("scalar", dt, None)


class ToolBackend:
    """Emission policy for one HLS tool.

    Subclasses must not change *what* the generators compute, only how it is
    spelled. The Vitis subclass is required to reproduce the pre-refactor output
    byte-for-byte; see the regression gate in the plan.
    """

    name = None

    # -- types -------------------------------------------------------------

    def type_decl(self, data_type):
        """The C++ type as it appears in generated declarations."""
        raise NotImplementedError

    def type_suffix(self, data_type):
        """Sanitized form used to build unique function names."""
        raise NotImplementedError

    # -- includes ----------------------------------------------------------

    def includes_top_cpp(self):
        raise NotImplementedError

    def includes_top_h(self):
        raise NotImplementedError

    def includes_tb(self):
        raise NotImplementedError

    # -- pragmas -----------------------------------------------------------

    def open_loop(self, header, factor):
        """Return the full loop opening, unroll directive included.

        `header` is the bare `for (...)` text with no trailing brace.
        """
        raise NotImplementedError

    def array_partition(self, var, factor, dim):
        """Return the in-body array-partition directive for `var`, or ""."""
        raise NotImplementedError

    def interface(self, drams):
        """Return the top-level interface pragma lines (may be empty)."""
        raise NotImplementedError

    # -- build script ------------------------------------------------------

    def emit_script(self, drams, target, clock_period, tasks, output_filename):
        raise NotImplementedError

    def run_cmd(self):
        """argv used to invoke the tool inside a design directory."""
        raise NotImplementedError


def effective_pragma_factor(requested_factor, concrete_dim):
    """Clamp an unroll/partition factor to the loop bound it applies to.

    Lifted from `scale_models/generate_code.py` (the only place in the repo where
    pragma factors were already funnelled through a helper) so every backend can
    share it. Not applied on the Vitis path — see `VitisBackend.open_loop`.
    """
    if requested_factor <= 1 or concrete_dim <= 1:
        return 1
    return min(requested_factor, concrete_dim)
