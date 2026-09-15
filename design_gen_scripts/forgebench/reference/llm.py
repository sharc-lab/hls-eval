"""Float64 llm oracle adapted from pinned upstream verification.

Local changes: strict buffer/initialization checks and float64 arithmetic.
Convolution uses vectorized spatial contractions for full-size base configs.
"""

import re

import numpy as np

from reference.activations import apply_activation

_SLICE_RE = re.compile(r"^\s*([A-Za-z_]\w*)\s*\[\s*(\d+)\s*\]\s*$")


def _prod(dims):
    out = 1
    for d in dims:
        out *= d
    return out


def _resolve(arrays, arg):
    """Return the ndarray referenced by `arg`, honoring a `NAME[idx]` row slice.

    A bare name returns the whole array. `NAME[idx]` returns row `idx` (matches the
    C where `weights[idx]` decays to a row pointer of a [rows][cols] array).
    """
    m = _SLICE_RE.match(arg)
    if m:
        return arrays[m.group(1)][int(m.group(2))]
    return arrays[arg]


def _read(arrays, name, shape):
    source = _resolve(arrays, name)
    n = _prod(shape)
    if source.size < n:
        raise ValueError(f"{name}: read {n} exceeds buffer {source.size}")
    result = source.reshape(-1)[:n].reshape(shape).astype(np.float64)
    if not np.isfinite(result).all():
        raise ValueError(f"{name}: read of uninitialized/nonfinite data")
    return result


def _write(arrays, name, value):
    target = _resolve(arrays, name)
    value = np.asarray(value, dtype=np.float64).reshape(-1)
    if target.size < value.size:
        raise ValueError(f"{name}: write {value.size} exceeds buffer {target.size}")
    target.reshape(-1)[: value.size] = value


def _op_copy(op, arrays):
    _write(arrays, op["args"][1], _read(arrays, op["args"][0], op["dims"]))


def _op_matmul(op, arrays):
    # C: output[i][j] = (bias|0); output[i][j] += input[i][k] * weights[j][k]
    # => output = input @ weights.T, weights is [DIM_OUT][DIM_IN].
    S, DIN, DOUT = op["dims"]
    use_bias = op["func_info"][1]
    if use_bias:
        a, w, bias, out = op["args"]
    else:
        a, w, out = op["args"][0], op["args"][1], op["args"][2]
        bias = None
    res = (_read(arrays, a, (S, DIN)) @ _read(arrays, w, (DOUT, DIN)).T).astype(
        np.float64
    )
    if bias is not None:
        res = (res + _read(arrays, bias, (DOUT,))).astype(np.float64)
    _write(arrays, out, res)


def _op_layernorm(op, arrays):
    S, DIM = op["dims"][0], op["dims"][1]
    eps = np.float64(op["dims"][2])
    a, gamma, beta, out = op["args"]
    x = _read(arrays, a, (S, DIM))
    g = _read(arrays, gamma, (DIM,))
    b = _read(arrays, beta, (DIM,))
    mean = x.mean(axis=1, keepdims=True).astype(np.float64)
    var = (((x - mean) ** 2).mean(axis=1, keepdims=True)).astype(np.float64)
    norm = ((x - mean) / np.sqrt(var + eps)).astype(np.float64)
    res = (g * norm + b).astype(np.float64)
    _write(arrays, out, res)


def _op_rmsnorm(op, arrays):
    S, DIM = op["dims"][0], op["dims"][1]
    eps = np.float64(op["dims"][2])
    a, gamma, out = op["args"]
    x = _read(arrays, a, (S, DIM))
    g = _read(arrays, gamma, (DIM,))
    rms = np.sqrt((x * x).mean(axis=1, keepdims=True) + eps).astype(np.float64)
    res = (g * x / rms).astype(np.float64)
    _write(arrays, out, res)


def _op_activation(op, arrays):
    S, DIM = op["dims"]
    act_name = op["func_info"][1]
    params = op["func_info"][2:]  # extra activation parameters, e.g. elu alpha
    a, out = op["args"]
    _write(arrays, out, apply_activation(act_name, _read(arrays, a, (S, DIM)), params))


def _op_dropout(op, arrays):
    # Inference-time dropout follows the branch template: identity.
    S, DIM = op["dims"]
    a, out = op["args"][0], op["args"][1]
    _write(arrays, out, _read(arrays, a, (S, DIM)))


def _op_matrix_add(op, arrays):
    S, DIM = op["dims"][0], op["dims"][1]
    a, b, out = op["args"]
    res = (_read(arrays, a, (S, DIM)) + _read(arrays, b, (S, DIM))).astype(np.float64)
    _write(arrays, out, res)


def _op_elementwise_mult(op, arrays):
    S, DIM = op["dims"][0], op["dims"][1]
    a, b, out = op["args"]
    res = (_read(arrays, a, (S, DIM)) * _read(arrays, b, (S, DIM))).astype(np.float64)
    _write(arrays, out, res)


def _apply_rope(mat, num_heads, head_dim):
    """RoPE exactly as the emitted C: theta = 10000^(-d/head_dim) for d=0,2,...

    Pair (idx, idx+1) with idx = h*head_dim + d rotated by angle = seq * theta.
    `mat` is [SEQ][num_heads*head_dim]; rotates in place, returns `mat`.
    """
    seq = mat.shape[0]
    out = mat.copy()
    for s in range(seq):
        for h in range(num_heads):
            for d in range(0, head_dim, 2):
                idx = h * head_dim + d
                theta = np.float64(10000.0) ** np.float64(-(float(d) / float(head_dim)))
                angle = np.float64(s) * theta
                c = np.float64(np.cos(angle))
                sn = np.float64(np.sin(angle))
                x0 = mat[s, idx]
                x1 = mat[s, idx + 1]
                out[s, idx] = x0 * c - x1 * sn
                out[s, idx + 1] = x0 * sn + x1 * c
    return out.astype(np.float64)


def _stable_softmax_1d(v):
    v = v.astype(np.float64)
    m = np.max(v)
    e = np.exp(v - m).astype(np.float64)
    return (e / np.sum(e)).astype(np.float64)


def _op_mha(op, arrays):
    S, DIN, NH, HD = op["dims"]
    DOUT = NH * HD
    use_rope = op["func_info"][1]
    a, wq, wk, wv, out = op["args"][0:5]
    groups = int(op["args"][5])

    x = _read(arrays, a, (S, DIN))
    Wq = _read(arrays, wq, (DOUT, DIN))
    Wk = _read(arrays, wk, (DOUT, DIN))
    Wv = _read(arrays, wv, (DOUT, DIN))
    Q = (x @ Wq.T).astype(np.float64)
    K = (x @ Wk.T).astype(np.float64)
    V = (x @ Wv.T).astype(np.float64)

    if use_rope:
        Q = _apply_rope(Q, NH, HD)
        K = _apply_rope(K, NH, HD)

    scale = np.float64(1.0) / np.float64(np.sqrt(float(HD)))
    output = np.zeros((S, DOUT), dtype=np.float64)

    # Require every declared head to be computed.
    if groups <= 0 or NH % groups:
        raise ValueError("Attention groups must divide the number of heads")
    heads_per_group = NH // groups
    for g in range(groups):
        for h in range(heads_per_group):
            head = g * heads_per_group + h
            sl = slice(head * HD, head * HD + HD)
            qh = Q[:, sl]
            kh = K[:, sl]
            vh = V[:, sl]
            scores = (qh @ kh.T).astype(np.float64) * scale  # [S,S], no causal mask
            for i in range(S):
                p = _stable_softmax_1d(scores[i])
                output[i, sl] = (p @ vh).astype(np.float64)
    _write(arrays, out, output)


def _op_swa(op, arrays):
    S, DIN, NH, HD = op["dims"]
    DOUT = NH * HD
    use_rope = op["func_info"][1]
    a, wq, wk, wv, out = op["args"][0:5]
    window = int(op["args"][5])

    x = _read(arrays, a, (S, DIN))
    Wq = _read(arrays, wq, (DOUT, DIN))
    Wk = _read(arrays, wk, (DOUT, DIN))
    Wv = _read(arrays, wv, (DOUT, DIN))
    Q = (x @ Wq.T).astype(np.float64)
    K = (x @ Wk.T).astype(np.float64)
    V = (x @ Wv.T).astype(np.float64)

    if use_rope:
        Q = _apply_rope(Q, NH, HD)
        K = _apply_rope(K, NH, HD)

    scale = np.float64(1.0) / np.float64(np.sqrt(float(HD)))
    output = np.zeros((S, DOUT), dtype=np.float64)

    for h in range(NH):
        sl = slice(h * HD, h * HD + HD)
        qh = Q[:, sl]
        kh = K[:, sl]
        vh = V[:, sl]
        for i in range(S):
            start = max(0, i - window)
            end = min(S - 1, i + window)  # inclusive, matches C
            idxs = np.arange(start, end + 1)
            scores = (qh[i] @ kh[idxs].T).astype(np.float64) * scale
            p = _stable_softmax_1d(scores)
            output[i, sl] = (p @ vh[idxs]).astype(np.float64)
    _write(arrays, out, output)


_DISPATCH = {
    "load": _op_copy,
    "store": _op_copy,
    "matmul": _op_matmul,
    "mha": _op_mha,
    "swa": _op_swa,
    "layernorm": _op_layernorm,
    "rmsnorm": _op_rmsnorm,
    "activation": _op_activation,
    "dropout": _op_dropout,
    "matrix_add": _op_matrix_add,
    "elementwise_mult": _op_elementwise_mult,
}


def run(ops, arrays):
    """Walk ops in insertion order, mutating `arrays` (name -> np.ndarray) in place."""
    for op_name, op in ops.items():
        fn = op["func_name"]
        if fn not in _DISPATCH:
            raise NotImplementedError(f"llm golden: unsupported op '{fn}' ({op_name})")
        _DISPATCH[fn](op, arrays)
