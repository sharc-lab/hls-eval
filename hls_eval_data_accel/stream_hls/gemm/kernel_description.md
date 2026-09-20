## gemm

General matrix multiplication with a scaled accumulate term, written to a separate output
matrix. The scalars are fixed constants inside the kernel, not arguments.

Top-Level Function: `forward`

Arguments, in order:

- `A`: `float[200][240]`, $NI \times NK$ matrix. Input.
- `B`: `float[240][220]`, $NK \times NJ$ matrix. Input.
- `C`: `float[200][220]`, $NI \times NJ$ matrix. Input.
- `D`: `float[200][220]`, $NI \times NJ$ matrix. Output, where $D = \alpha AB + \beta C$
  with $\alpha = 0.5$ and $\beta = 0.1$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
