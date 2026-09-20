## k2mm

Linear algebra kernel that consists of two chained matrix multiplications followed by a scaled
accumulate, written to a separate output matrix (a 2mm). The scalars are fixed constants inside
the kernel, not arguments.

Top-Level Function: `forward`

Arguments, in order:

- `A`: `float[180][210]`, $P \times Q$ matrix. Input.
- `B`: `float[210][190]`, $Q \times R$ matrix. Input.
- `C`: `float[190][220]`, $R \times S$ matrix. Input.
- `D`: `float[180][220]`, $P \times S$ matrix. Input.
- `E`: `float[180][220]`, $P \times S$ matrix. Output, where $E = \alpha (AB)C + \beta D$
  with $\alpha = 0.5$ and $\beta = 0.1$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
