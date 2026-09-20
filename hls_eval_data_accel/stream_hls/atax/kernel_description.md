## atax

Computes $A^T$ times $Ax$, in a dataflow (streaming) form.

Top-Level Function: `forward`

Arguments, in order:

- `A`: `float[390][410]`, the $M \times N$ matrix ($M=390$, $N=410$). Input.
- `x`: `float[410]`, vector of length $N$. Input.
- `y`: `float[410]`, vector of length $N$. Output, where $y = A^T(Ax)$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
