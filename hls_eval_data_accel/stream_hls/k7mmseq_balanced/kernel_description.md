## k7mmseq_balanced

A sequence of seven chained matrix multiplications, where all eight matrices are the same size
($64 \times 64$), so every multiplication does the same amount of work (a "balanced" chain).

Top-Level Function: `forward`

Arguments, in order:

- `M0`, `M1`, `M2`, `M3`, `M4`, `M5`, `M6`, `M7`: `float[64][64]` matrices. Inputs.
- `R`: `float[64][64]` matrix. Output, where $R = M_0 M_1 M_2 M_3 M_4 M_5 M_6 M_7$, evaluated
  left to right: $(((((((M_0 M_1) M_2) M_3) M_4) M_5) M_6) M_7)$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
