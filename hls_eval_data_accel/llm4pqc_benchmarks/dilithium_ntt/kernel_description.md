## dilithium_ntt

Computes the forward number-theoretic transform (NTT) used by
CRYSTALS-Dilithium (reference `ntt.c: ntt`), an in-place, 8-layer
Cooley-Tukey NTT over the ring $\mathbb{Z}_{8380417}[X]/(X^{256}+1)$. Unlike
Kyber's NTT, Dilithium's is a *complete* transform: all 8 layers run, so the
256 output coefficients are (up to the representation caveat below) 256
independent evaluations of the input polynomial.

Top-Level Function: `dilithium_ntt`

Input/Output:

- `a`: array of 256 `int32_t` coefficients, transformed in place. Input
  coefficients are in $[0, 8380417)$. The output is the upstream
  implementation's signed, lazily-reduced representation — coefficients are
  **not** normalized to $[0, 8380417)$ and no reduction is performed after
  the final additions/subtractions; correctness must be checked modulo
  $q = 8380417$ (reduce each output coefficient into $[0, 8380417)$ before
  comparing).

Each of the 8 layers halves the butterfly span `len` (128, 64, ..., 1) and
combines coefficient pairs `(a[j], a[j+len])` using a fixed-point Montgomery
multiplication by a precomputed twiddle factor (`zetas`, indexed
sequentially across all layers) and Montgomery reduction modulo $q$:

$$
t = \text{MontgomeryReduce}(zeta \cdot a(j+len)), \qquad
a(j+len) = a(j) - t, \qquad a(j) = a(j) + t
$$

An independent oracle for validating output: output coefficient `a[i]`,
reduced mod 8380417, must equal the input polynomial evaluated (mod
8380417) at $1753^{2\,\text{bitrev}_8(i)+1}$.
