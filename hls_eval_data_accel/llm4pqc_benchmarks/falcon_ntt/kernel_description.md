## falcon_ntt

Computes the forward number-theoretic transform used by Falcon's signature
verification path (reference `vrfy.c: mq_NTT`), an in-place, 10-layer
Cooley-Tukey NTT over the ring $\mathbb{Z}_{12289}[X]/(X^{1024}+1)$
($\text{logn} = 10$, so $N = 1024$).

Top-Level Function: `falcon_ntt`

Input/Output:

- `a`: array of 1024 `uint16_t` coefficients, transformed in place. Input
  and output coefficients are both fully reduced to $[0, 12289)$ (unlike
  the Kyber/Dilithium NTTs, this transform normalizes every result, so no
  extra modular reduction is needed to compare output values).

Each of the 10 layers halves the butterfly span and combines coefficient
pairs using a precomputed twiddle factor (`GMb`, a table of powers of a
primitive root of unity mod 12289 in bit-reversed order) and a
Montgomery-style multiplication modulo $q = 12289$:

$$
u = a(j), \qquad v = \text{MontyMul}(a(j+ht),\, GMb(m+i)) \bmod q
$$
$$
a(j) = (u+v) \bmod q, \qquad a(j+ht) = (u-v) \bmod q
$$

where `ht` is half the current butterfly span and `GMb(m+i)` is the twiddle
factor for that layer/block.

An independent oracle for validating output: output coefficient `a[i]` must
equal the input polynomial evaluated (mod 12289) at
$7^{2\,\text{bitrev}_{10}(i)+1}$.
