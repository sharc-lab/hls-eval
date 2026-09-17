## falcon_sampler

Draws one sample from Falcon's discrete Gaussian sampler over the integers
(reference `sign.c: Zf(sampler)`), the per-coordinate sampling primitive
used when signing with Falcon. Given a target center $\mu$ and standard
deviation $\sigma$ (passed as $1/\sigma$), it returns one integer $z$ drawn
so that, over many draws, $z$ is approximately distributed as a discrete
Gaussian centered at $\mu$ with standard deviation $\sigma$.

Top-Level Function: `falcon_sampler`

Inputs:

- `mu`: the center of the target Gaussian.
- `isigma`: $1/\sigma$, the reciprocal of the target standard deviation.
  Valid range: $1 < \sigma < 2$.
- `sigma_min`: a fixed minimum-sigma parameter used to rescale the
  acceptance probability in rejection sampling ($0 < \sigma_{\min} \le
  \sigma$).
- `buf` (512 bytes), `ptr` (1 word), `state` (256 bytes): the caller-owned
  PRNG's output buffer, read cursor, and internal generator state. This
  must already be initialized from Falcon's reference ChaCha20-based PRNG
  before the first call (seeding is outside this function); `ptr[0]` must
  be less than 512 on entry.

Outputs:

- Return value: the sampled integer $z$.
- `buf`, `ptr`, `state`: updated in place to reflect however many
  pseudo-random bytes this draw consumed (including a full PRNG refill of
  `buf`/`state` if the draw exhausts the current buffer) — the caller must
  preserve and pass these back on the next draw to get a correct sequence.

Algorithm: split $\mu = s + r$ with $s$ integer and $0 \le r < 1$. Draw a
half-Gaussian sample $z_0 \ge 0$ (via a fixed cumulative-probability table
over a uniform random 72-bit value), randomly pick a bimodal bit $b$, and
set a candidate $z = b + (2b-1) z_0$. Accept the candidate with the
Bernoulli-style probability $\exp(-x)$, where
$x = \frac{(z-r)^2}{2\sigma^2} - \frac{(z-z_0')^2}{2\sigma_0^2}$
compares the target Gaussian density at $z$ against the (broader,
easier-to-sample) proposal density it was drawn from; if rejected, redraw
$z_0$/$b$ and retry (the rejection loop has no fixed iteration bound). On
acceptance, return $s + z$.

Arithmetic note: `mu`, `isigma`, and `sigma_min` arrive as `double`, but all
of $r$, $\sigma$, $\sigma_0$, and the Bernoulli exponent $x$ are computed
internally using Falcon's own `fpr` type — its integer-only software
emulation of IEEE-754 binary64 (bit-identical to a real `double`'s
sign/exponent/mantissa layout, but every add/multiply/`exp` is computed by
explicit integer/bit-shift arithmetic rather than a hardware FPU op).
Reproducing this arithmetic bit-for-bit (not just "close enough" native
double math) is necessary to reproduce the same sample sequence and PRNG
state for a given seed.
