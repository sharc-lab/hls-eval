"""Float64 gemm oracle adapted from pinned upstream verification.

Local changes: strict buffer/initialization checks and float64 arithmetic.
Convolution uses vectorized spatial contractions for full-size base configs.
"""

import numpy as np

from reference.activations import apply_activation

GEMM_OPS = {"gemm", "vmm", "mmv", "dot_product"}


def _prod(dims):
    out = 1
    for d in dims:
        out *= d
    return out


def _read(arrays, name, shape):
    source = arrays[name]
    n = _prod(shape)
    if source.size < n:
        raise ValueError(f"{name}: read {n} exceeds buffer {source.size}")
    result = source.reshape(-1)[:n].reshape(shape).astype(np.float64)
    if not np.isfinite(result).all():
        raise ValueError(f"{name}: read of uninitialized/nonfinite data")
    return result


def _write(arrays, name, value):
    target = arrays[name]
    value = np.asarray(value, dtype=np.float64).reshape(-1)
    if target.size < value.size:
        raise ValueError(f"{name}: write {value.size} exceeds buffer {target.size}")
    target.reshape(-1)[: value.size] = value


def _op_copy(op, arrays):
    _write(arrays, op["args"][1], _read(arrays, op["args"][0], op["dims"]))


def _op_gemm(op, arrays):
    M, N, K = op["dims"]
    _order, _unroll, with_bias, _inline = op["func_info"]
    a, b, bias, out = op["args"]
    res = (_read(arrays, a, (M, N)) @ _read(arrays, b, (N, K))).astype(np.float64)
    if with_bias:
        res = (res + _read(arrays, bias, (M, K))).astype(np.float64)
    _write(arrays, out, res)


def _op_mmv(op, arrays):
    M, N = op["dims"]
    _order, _unroll, with_bias, _inline = op["func_info"]
    a, b, bias, out = op["args"]
    res = (_read(arrays, a, (M, N)) @ _read(arrays, b, (N,))).astype(np.float64)
    if with_bias:
        res = (res + _read(arrays, bias, (M,))).astype(np.float64)
    _write(arrays, out, res)


def _op_vmm(op, arrays):
    M, N = op["dims"]
    _order, _unroll, with_bias, _inline = op["func_info"]
    a, b, bias, out = op["args"]
    res = (_read(arrays, a, (M, N)).T @ _read(arrays, b, (M,))).astype(np.float64)
    if with_bias:
        res = (res + _read(arrays, bias, (N,))).astype(np.float64)
    _write(arrays, out, res)


def _op_dot(op, arrays):
    M = op["dims"][0]
    _unroll, with_bias, _inline = op["func_info"]
    a, b, bias, out = op["args"]
    res = np.array(
        [np.dot(_read(arrays, a, (M,)), _read(arrays, b, (M,)))], dtype=np.float64
    )
    if with_bias:
        res = (res + _read(arrays, bias, (1,))).astype(np.float64)
    _write(arrays, out, res)


def _op_activation(op, arrays):
    H, W = op["dims"]
    act_name = op["func_info"][1]
    params = op["func_info"][2:]  # extra activation parameters, e.g. elu alpha
    in_name, out_name = op["args"]
    _write(
        arrays,
        out_name,
        apply_activation(act_name, _read(arrays, in_name, (H, W)), params),
    )


_DISPATCH = {
    "load": _op_copy,
    "store": _op_copy,
    "gemm": _op_gemm,
    "mmv": _op_mmv,
    "vmm": _op_vmm,
    "dot_product": _op_dot,
    "activation": _op_activation,
}


def run(ops, arrays):
    """Walk ops in insertion order, mutating `arrays` (name -> np.ndarray) in place."""
    for op_name, op in ops.items():
        fn = op["func_name"]
        if fn not in _DISPATCH:
            raise NotImplementedError(f"gemm golden: unsupported op '{fn}' ({op_name})")
        _DISPATCH[fn](op, arrays)
