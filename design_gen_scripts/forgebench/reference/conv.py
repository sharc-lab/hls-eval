"""Float64 conv oracle adapted from pinned upstream verification.

Local changes: strict buffer/initialization checks and float64 arithmetic.
Convolution uses vectorized spatial contractions for full-size base configs.
"""

import numpy as np

from reference.activations import apply_activation

CONV_OPS = {"conv", "batchnorm", "maxpool", "adaptive_avgpool"}


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


def _op_conv(op, arrays):
    d = op["dims"]
    C_IN, C_OUT, H_IN, W_IN, H_OUT, W_OUT, K, PAD, STRIDE = d[:9]
    _template, func_type, with_bias = op["func_info"]

    # For group_conv2d the generator appends the groups count as the final arg
    # (matching conv/auto_generate_json.py: conv_args.append(groups)). The emitted
    # C still declares the kernel as [C_OUT][C_IN][K][K] (full C_IN) and only reads
    # the block-diagonal slice per group, so the weight shape is unchanged.
    args = list(op["args"])
    groups = 1
    if func_type == "group_conv2d":
        groups = int(args.pop())  # trailing groups count

    if with_bias:
        in_name, w_name, b_name, out_name = args
    else:
        in_name, w_name, out_name = args
        b_name = None

    x = _read(arrays, in_name, (C_IN, H_IN, W_IN))
    w = _read(arrays, w_name, (C_OUT, C_IN, K, K))

    # Initialize output to bias (per out-channel) or zero, matching the C.
    if with_bias:
        bias = _read(arrays, b_name, (C_OUT,))
        out = (
            np.repeat(bias, H_OUT * W_OUT)
            .reshape(C_OUT, H_OUT, W_OUT)
            .astype(np.float64)
        )
    else:
        out = np.zeros((C_OUT, H_OUT, W_OUT), dtype=np.float64)

    ci_per_g = C_IN // groups
    co_per_g = C_OUT // groups

    # Cross-correlation; contract channels over all spatial sites at once.
    # Configs explicitly specify output extents. The kernel treats every
    # sample outside the logical input as zero, including extra output sites.
    bottom = max(PAD, (H_OUT - 1) * STRIDE + K - H_IN - PAD)
    right = max(PAD, (W_OUT - 1) * STRIDE + K - W_IN - PAD)
    padded = np.pad(x, ((0, 0), (PAD, bottom), (PAD, right)))
    for kh in range(K):
        for kw in range(K):
            patch = padded[
                :, kh : kh + H_OUT * STRIDE : STRIDE, kw : kw + W_OUT * STRIDE : STRIDE
            ]
            if patch.shape != (C_IN, H_OUT, W_OUT):
                raise ValueError("Convolution output extent exceeds padded input")
            for g in range(groups):
                ci0, ci1 = g * ci_per_g, (g + 1) * ci_per_g
                co0, co1 = g * co_per_g, (g + 1) * co_per_g
                out[co0:co1] += (
                    w[co0:co1, ci0:ci1, kh, kw] @ patch[ci0:ci1].reshape(ci_per_g, -1)
                ).reshape(co_per_g, H_OUT, W_OUT)
    _write(arrays, out_name, out)


def _op_batchnorm(op, arrays):
    C, H, W = op["dims"]
    _template, eps = op["func_info"]
    in_name, w_name, out_name = op["args"]

    x = _read(arrays, in_name, (C, H, W))
    weights = _read(arrays, w_name, (4, C))  # gamma, beta, mean, variance
    gamma = weights[0].reshape(C, 1, 1)
    beta = weights[1].reshape(C, 1, 1)
    mean = weights[2].reshape(C, 1, 1)
    var = weights[3].reshape(C, 1, 1)

    norm = (x - mean) / np.sqrt(var + np.float64(eps))
    out = (gamma * norm + beta).astype(np.float64)
    _write(arrays, out_name, out)


def _op_activation(op, arrays):
    C, H, W = op["dims"]
    act_name = op["func_info"][1]
    params = op["func_info"][2:]  # extra activation parameters, e.g. elu alpha
    in_name, out_name = op["args"]
    x = _read(arrays, in_name, (C, H, W))
    _write(arrays, out_name, _apply_conv_activation(act_name, x, params))


def _apply_conv_activation(name, x, params=()):
    """Conv-domain activations. Softmax here is over the CHANNEL axis (axis 0),
    which differs from the shared row-wise softmax; the rest reuse the shared
    textbook oracles."""
    key = name.lower()
    if key == "softmax":
        x = x.astype(np.float64)
        shifted = x - np.max(x, axis=0, keepdims=True)
        e = np.exp(shifted)
        return (e / np.sum(e, axis=0, keepdims=True)).astype(np.float64)
    if key == "hardsigmoid":
        return np.clip((x + 3.0) / 6.0, 0.0, 1.0).astype(np.float64)
    if key == "hardswish":
        return (x * np.clip((x + 3.0) / 6.0, 0.0, 1.0)).astype(np.float64)
    return apply_activation(name, x, params)


def _op_maxpool(op, arrays):
    C, H_IN, W_IN, H_OUT, W_OUT, K_H, K_W, S_H, S_W = op["dims"]
    in_name, out_name = op["args"]
    x = _read(arrays, in_name, (C, H_IN, W_IN))
    out = np.empty((C, H_OUT, W_OUT), dtype=np.float64)
    for c in range(C):
        for i in range(H_OUT):
            for j in range(W_OUT):
                r0, c0 = i * S_H, j * S_W
                window = x[c, r0 : r0 + K_H, c0 : c0 + K_W]
                out[c, i, j] = window.max()
    _write(arrays, out_name, out)


def _op_adaptive_avgpool(op, arrays):
    C, H_IN, W_IN, H_OUT, W_OUT = op["dims"]
    in_name, out_name = op["args"]
    x = _read(arrays, in_name, (C, H_IN, W_IN))
    out = np.zeros((C, H_OUT, W_OUT), dtype=np.float64)
    for oh in range(H_OUT):
        h_start = int(np.floor(oh * H_IN / H_OUT))
        h_end = min(int(np.ceil((oh + 1) * H_IN / H_OUT)), H_IN)
        for ow in range(W_OUT):
            w_start = int(np.floor(ow * W_IN / W_OUT))
            w_end = min(int(np.ceil((ow + 1) * W_IN / W_OUT)), W_IN)
            region = x[:, h_start:h_end, w_start:w_end]
            count = (h_end - h_start) * (w_end - w_start)
            if count > 0:
                out[:, oh, ow] = region.reshape(C, -1).sum(axis=1) / np.float64(count)
    _write(arrays, out_name, out)


def _op_matrix_add(op, arrays):
    C, H, W = op["dims"]
    in1, in2, out_name = op["args"]
    a = _read(arrays, in1, (C, H, W))
    b = _read(arrays, in2, (C, H, W))
    _write(arrays, out_name, (a + b).astype(np.float64))


_DISPATCH = {
    "load": _op_copy,
    "store": _op_copy,
    "conv": _op_conv,
    "batchnorm": _op_batchnorm,
    "activation": _op_activation,
    "maxpool": _op_maxpool,
    "adaptive_avgpool": _op_adaptive_avgpool,
    "matrix_add": _op_matrix_add,
}


def run(ops, arrays):
    """Walk ops in insertion order, mutating `arrays` (name -> np.ndarray) in place."""
    for op_name, op in ops.items():
        fn = op["func_name"]
        if fn not in _DISPATCH:
            raise NotImplementedError(f"conv golden: unsupported op '{fn}' ({op_name})")
        _DISPATCH[fn](op, arrays)
