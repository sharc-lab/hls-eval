## kyber_ntt

Computes the forward number-theoretic transform (NTT) used by CRYSTALS-Kyber
(reference `ntt.c: ntt`), an in-place, 7-layer Cooley-Tukey NTT over the ring
$\mathbb{Z}_{3329}[X]/(X^{256}+1)$ (this is Kyber's *incomplete* NTT: it stops
one layer short of a full transform, leaving the result as 128 degree-2
"blocks" rather than 256 independent point evaluations).

Top-Level Function: `kyber_ntt`

Input/Output:

- `a`: array of 256 `int16_t` coefficients, transformed in place. Input
  coefficients are in $[0, 3329)$. The output is the upstream
  implementation's signed, lazily-reduced representation — coefficients are
  **not** all normalized to $[0, 3329)$ and may be negative or exceed $q$ in
  magnitude within the implementation's stated bounds; correctness must be
  checked modulo $q = 3329$ (reduce each output coefficient into
  $[0, 3329)$ before comparing).

Each of the 7 layers halves the "butterfly span" `len` (128, 64, ..., 2) and
combines coefficient pairs `(r[j], r[j+len])` using a fixed-point Montgomery
multiplication by a precomputed twiddle factor (`zetas`, indexed
sequentially across all layers) and Montgomery reduction modulo $q$, in the
standard decimation-in-time NTT butterfly pattern:

$$
t = \text{MontgomeryReduce}(zeta \cdot r(j+len)), \qquad
r(j+len) = r(j) - t, \qquad r(j) = r(j) + t
$$

An independent oracle for validating output: for output index $i$, let
$b = \lfloor i/2 \rfloor$; then `a[2b]` and `a[2b+1]`, reduced mod 3329, must
equal the input polynomial evaluated (mod 3329) at
$17^{2 \cdot \text{bitrev}_7(b)+1}$ and its negation, respectively (the two
roots of the degree-2 factor for that block) — equivalently, any check that
evaluates the original polynomial at the 128 primitive roots
$17^{2\,\text{bitrev}_7(b)+1} \bmod 3329$ and compares against the
corresponding coefficient pair is a valid correctness check.
