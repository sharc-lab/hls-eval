## k3mm

Linear algebra kernel that consists of three matrix multiplications (a 3mm): two independent
products feeding a third.

Top-Level Function: `forward`

Arguments, in order:

- `A`: `float[180][200]`, $P \times Q$ matrix. Input.
- `B`: `float[200][190]`, $Q \times R$ matrix. Input.
- `C`: `float[190][220]`, $R \times S$ matrix. Input.
- `D`: `float[220][210]`, $S \times T$ matrix. Input.
- `G`: `float[180][210]`, $P \times T$ matrix. Output, where $G = (AB)(CD)$.

All tensors are single-precision `float`, row-major. The outputs are checked elementwise against golden values with an absolute plus relative tolerance, so a different (float) summation order is acceptable.
