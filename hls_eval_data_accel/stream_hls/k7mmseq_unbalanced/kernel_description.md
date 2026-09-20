## k7mmseq_unbalanced

A sequence of seven chained matrix multiplications where the matrix shapes vary along the chain,
so each multiplication does a different amount of work (an "unbalanced" chain).

Top-Level Function: `forward`

Arguments, in order:

- `M0`: `float[64][32]`. Input.
- `M1`: `float[32][64]`. Input.
- `M2`: `float[64][64]`. Input.
- `M3`: `float[64][128]`. Input.
- `M4`: `float[128][128]`. Input.
- `M5`: `float[128][64]`. Input.
- `M6`: `float[64][32]`. Input.
- `M7`: `float[32][16]`. Input.
- `R`: `float[64][16]`. Output, where $R = M_0 M_1 M_2 M_3 M_4 M_5 M_6 M_7$, evaluated left to
  right: $(((((((M_0 M_1) M_2) M_3) M_4) M_5) M_6) M_7)$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
