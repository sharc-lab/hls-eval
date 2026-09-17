## falcon_fft

Computes Falcon's FFT over the reals (reference `fft.c: Zf(FFT)`): the
discrete Fourier-like transform Falcon uses to evaluate a degree-$N$
polynomial (taken modulo $X^N+1$) at the $N$ complex roots of $X^N+1$,
$\text{logn} = 9$ so $N = 512$.

Top-Level Function: `falcon_fft`

Input/Output:

- `a`: array of 512 `double`s, transformed in place.
  - **Input**: the coefficients of a degree-511 real polynomial.
  - **Output**: because the polynomial is real, its values at the 512 roots
    of $X^{512}+1$ come in conjugate pairs, so only half the spectrum is
    stored: `a[0..255]` hold the real parts and `a[256..511]` hold the
    imaginary parts of $f(w_j)$ for $j = 0, \ldots, 255$, where
    $w_j = \exp\!\big(i\pi(2j+1)/512\big)$. Each `a[i] + i \cdot a[i+256]` is
    one such complex value, but **not** in natural index order — see the
    oracle below for the exact index mapping. This is Falcon's standard
    packed FFT representation, not a plain complex array.

Let $w = \exp(i\pi/512)$ be a primitive 1024-th root of unity; the roots of
$X^{512}+1$ are $w_j = w^{2j+1}$ for $j = 0, \ldots, 511$, and
$w_{511-j} = \overline{w_j}$. The transform computes $f(w_j)$ for
$j = 0, \ldots, 255$ via the standard recursive/iterative radix-2 FFT
butterfly (complex multiply-add against a precomputed table of powers of
$w$ in bit-reversed order), exploiting $f(w_{511-j}) = \overline{f(w_j)}$ so
only half the outputs need to be computed or stored.

An independent oracle for validating output: for $0 \le i < 256$,
$a(i) + j \cdot a(i+256)$ must equal the input polynomial evaluated at
$\exp\!\big(j\pi(4\,\text{bitrev}_8(i)+1)/512\big)$, within a complex error
tolerance of $10^{-7} + 10^{-10}\cdot|\text{expected}|$.

Arithmetic note: the top-level `falcon_fft` interface is `double a[512]`, but
internally each value is carried as Falcon's own `fpr` type — its
integer-only software emulation of IEEE-754 binary64 (bit-identical to a
real `double`'s sign/exponent/mantissa layout, but every add/multiply is
computed by explicit integer/bit-shift arithmetic rather than a hardware FPU
op). Reproducing this arithmetic bit-for-bit (not just "close enough" native
double math) is part of matching the reference output.
