Kernel Description:
The `kernel_2mm` is a linear algebra kernel. It takes in seven inputs: two scalars `alpha` and `beta`, and four matrices `A`, `B`, `C`, and `D`. The kernel computes the matrix product `ABC` scaled by `alpha` and adds it to the matrix `D` scaled by `beta`. The result is stored in the matrix `E`, which is not explicitly passed as an output but is equivalent to the modified matrix `D`.

It takes the following as inputs,

- $\alpha, \beta$: scalars
- $A: P \times Q$ matrix
- $B: Q \times R$ matrix
- $C: R \times S$ matrix
- $D: P \times S$ matrix

and gives the following as output:

- $E: P \times S$ matrix, where $E = \alpha ABC + \beta D$

---

Top-Level Function: `kernel_2mm`

Complete Function Signature of the Top-Level Function:
`void kernel_2mm(double alpha, double beta, double tmp[16][18], double A[16][22], double B[22][18], double C[18][24], double D[16][24]);`

Inputs:
- `alpha`: a scalar value that scales the matrix product `ABC`
- `beta`: a scalar value that scales the matrix `D`
- `tmp`: a temporary matrix of size 16x18 used to store the intermediate result of the matrix product `AB`
- `A`: a matrix of size 16x22
- `B`: a matrix of size 22x18
- `C`: a matrix of size 18x24
- `D`: a matrix of size 16x24

Outputs:
- `D`: the modified matrix `D` which is the result of the computation `E = alpha * ABC + beta * D`

Important Data Structures and Data Types:
- `tmp`: a 2D array of size 16x18 used to store the intermediate result of the matrix product `AB`
- `A`, `B`, `C`, `D`: 2D arrays of sizes 16x22, 22x18, 18x24, and 16x24, respectively, used to store the input matrices

Sub-Components:
- None