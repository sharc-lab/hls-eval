"""Textbook activation oracles shared across ForgeBench domains.

Golden-reference policy (see plan / feedback-golden-oracle): implement the
canonical/textbook definition. Deviate to match the emitted C **only** where the
C deliberately implements a widely-used *variant*; each such deviation is noted
inline so it can be reported in the verification README.

Deliberate variants matched here:
  - gelu: tanh approximation (matches gemm/2D_activations_template.cpp), NOT the
    exact erf-based gelu.
  - softmax: row-wise over the last axis (matches the C). We subtract the row max
    for numerical stability; softmax is shift-invariant so this is mathematically
    identical to the C's raw-exp form and stays within float tolerance.

Several activations in the C template take extra scalar parameters (leaky_relu
alpha, elu alpha, selu alpha/lambda, relu6 cap, prelu alpha, rrelu lower/upper,
thresholded_relu theta). The generators emit those arguments at the call site,
defaulting to the canonical values in each domain's `ACTIVATION_EXTRA_PARAMS` and
overridable per config via `func_info[2:]`; `apply_activation` takes the same
values so the oracle and the emitted C stay in step. The defaults below and the
generators' defaults must be kept in sync.
"""

import numpy as np

_SQRT_2_OVER_PI = np.float64(np.sqrt(2.0 / np.pi))


def relu(x):
    return np.maximum(x, 0.0).astype(np.float64)


def relu6(x, cap=6.0):
    return np.clip(x, 0.0, cap).astype(np.float64)


def leaky_relu(x, alpha=0.01):
    return np.where(x >= 0, x, alpha * x).astype(np.float64)


def prelu(x, alpha=0.25):
    return np.where(x >= 0, x, alpha * x).astype(np.float64)


def rrelu(x, lower=1.0 / 8, upper=1.0 / 3):
    ralpha = (lower + upper) / 2.0
    return np.where(x >= 0, x, ralpha * x).astype(np.float64)


def thresholded_relu(x, theta=1.0):
    return np.where(x > theta, x, 0.0).astype(np.float64)


def sigmoid(x):
    return (1.0 / (1.0 + np.exp(-x))).astype(np.float64)


def tanh_act(x):
    return np.tanh(x).astype(np.float64)


def elu(x, alpha=1.0):
    return np.where(x >= 0, x, alpha * (np.exp(x) - 1.0)).astype(np.float64)


def selu(x, alpha=1.6732632423543772, lam=1.0507009873554805):
    return np.where(x >= 0, lam * x, lam * alpha * (np.exp(x) - 1.0)).astype(np.float64)


def gelu(x):
    # Deliberate variant: tanh approximation, matching the emitted C.
    x = x.astype(np.float64)
    inner = _SQRT_2_OVER_PI * (x + np.float64(0.044715) * x * x * x)
    return (np.float64(0.5) * x * (1.0 + np.tanh(inner))).astype(np.float64)


def swish(x):
    return (x * sigmoid(x)).astype(np.float64)


def softmax(x):
    # Row-wise over the last axis (matches the C), stabilized by max-subtraction.
    x = x.astype(np.float64)
    shifted = x - np.max(x, axis=-1, keepdims=True)
    e = np.exp(shifted)
    return (e / np.sum(e, axis=-1, keepdims=True)).astype(np.float64)


def hardsigmoid(x):
    # Matches conv/activations_template.cpp: 0 for x<=-3, 1 for x>=3, else (x+3)/6.
    x = x.astype(np.float64)
    return np.clip((x + np.float64(3.0)) / np.float64(6.0), 0.0, 1.0).astype(np.float64)


def hardswish(x):
    # Matches conv/activations_template.cpp: x * hardsigmoid(x).
    x = x.astype(np.float64)
    return (x * hardsigmoid(x)).astype(np.float64)


# Map config activation names -> implementation. "tanh" and "tanh_act" both accepted.
_DISPATCH = {
    "relu": relu,
    "relu6": relu6,
    "leaky_relu": leaky_relu,
    "prelu": prelu,
    "rrelu": rrelu,
    "thresholded_relu": thresholded_relu,
    "sigmoid": sigmoid,
    "tanh": tanh_act,
    "tanh_act": tanh_act,
    "elu": elu,
    "selu": selu,
    "gelu": gelu,
    "swish": swish,
    "softmax": softmax,
    "hardsigmoid": hardsigmoid,
    "hardswish": hardswish,
}


def apply_activation(name, x, params=()):
    """Apply activation `name` to `x`.

    `params` are the activation's extra scalar parameters, taken from the config's
    `func_info[2:]` (leaky_relu alpha, elu alpha, selu alpha/lambda, relu6 cap,
    prelu alpha, rrelu lower/upper, thresholded_relu theta). When empty, each
    oracle's default applies -- and those defaults are the same values the
    generators emit at the call site (ACTIVATION_EXTRA_PARAMS in each domain's
    generate_code.py). Activations that take no extra parameters ignore `params`.
    """
    key = name.lower()
    if key not in _DISPATCH:
        raise NotImplementedError(
            f"activation '{name}' not implemented in golden reference"
        )
    fn = _DISPATCH[key]
    if not params:
        return fn(x)
    if key not in _PARAMETERIZED:
        raise ValueError(
            f"activation '{name}' takes no extra parameters, got {list(params)}"
        )
    return fn(x, *[float(p) for p in params])


# Activations whose oracle accepts extra scalar parameters.
_PARAMETERIZED = {
    "relu6",
    "leaky_relu",
    "prelu",
    "rrelu",
    "thresholded_relu",
    "elu",
    "selu",
}
