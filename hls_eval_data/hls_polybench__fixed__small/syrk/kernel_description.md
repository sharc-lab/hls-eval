## syrk

Symmetric rank k update from updated BLAS.
It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A$: $N \times M$ matrix
- $C$: $N \times N$ symmetric matrix

and gives the following as output:

- $C_{out}$: $N \times N$ matrix, where $C_{out} = \alpha A A^T + \beta C$

Note that the output $C_{out}$ is to be stored in place of the input array $C$. The matrix $C$ is stored as a triangular matrix in BLAS, and the result is also triangular. The configurations used are `TRANS = 'N'` and `UPLO = 'L'` meaning the $A$ matrix is not transposed, and $C$ matrix stores the symmetric matrix as lower triangular matrix.
Storage/ordering contract: use original t_ap_fixed types and modes. For each i in increasing order, first multiply each lower C[i][j], j=0..i, by beta and store it in C's declared type. Then, for k=0..M-1 in increasing order, visit j=0..i and add alpha*A[i][k]*A[j][k] to stored C[i][j], storing into the declared type after each addition. Preserve the written multiplication association. A is preserved. Only lower C is a defined output; upper C is not part of the stored triangular result and is not graded.

Original numeric type: t_ap_fixed is exactly ap_fixed<32,16>, with the original SDK default AP_TRN quantization, AP_WRAP overflow and N=0 template settings. Retain that declared width, integer width and those conversion/storage points; the observable stored result is compared by its 32 raw bits.
