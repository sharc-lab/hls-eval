Kernel Description:
The GEMM (General Matrix-Matrix Multiplication) kernel is designed to perform matrix multiplication on two input matrices, producing a resulting product matrix. The kernel operates on double-precision floating-point data and is optimized for parallel execution, leveraging a nested loop structure to exploit data parallelism and reduce memory access patterns. The matrix multiplication is performed using the standard matrix multiplication algorithm, which can be represented by the following equation: 

$$
C_{ij} = \sum_{k=0}^{n-1} A_{ik} \times B_{kj}
$$

where $A$ and $B$ are the input matrices, $C$ is the resulting product matrix, and $n$ is the number of columns in the first matrix and the number of rows in the second matrix. The kernel is designed to work with matrices of size 64x64 elements, which are stored in row-major order, with each row contiguous in memory.

The kernel uses a nested loop structure, consisting of three loops: an outer loop, a middle loop, and an inner loop. The outer loop iterates over the rows of the input matrices, the middle loop iterates over the columns of the input matrices, and the inner loop performs the actual matrix multiplication, iterating over the elements of the input matrices and accumulating the products in a temporary variable. The kernel also uses a mechanism to calculate the memory addresses of the input and output matrices, using the loop counters to access the correct elements.

The kernel is designed to be efficient and scalable, with a focus on minimizing memory access patterns and maximizing parallelism. The use of a nested loop structure and the calculation of memory addresses using loop counters allows the kernel to be easily parallelized, making it suitable for execution on a variety of architectures, including GPUs and CPUs.

---

Top-Level Function: `gemm`

Complete Function Signature of the Top-Level Function:
`void gemm(double m1[4096], double m2[4096], double prod[4096]);`

Inputs:
- `m1`: A 2D matrix of size 64x64, represented as a 1D array of `double` values, with a total of 4096 elements. The matrix is stored in row-major order, with each row contiguous in memory.
- `m2`: A 2D matrix of size 64x64, represented as a 1D array of `double` values, with a total of 4096 elements. The matrix is stored in row-major order, with each row contiguous in memory.

Outputs:
- `prod`: A 2D matrix of size 64x64, represented as a 1D array of `double` values, with a total of 4096 elements. The matrix is stored in row-major order, with each row contiguous in memory.

Important Data Structures and Data Types:
- `TYPE`: A `double` data type, used to represent the elements of the input and output matrices.
- `N`: A constant integer value, representing the total number of elements in each matrix (4096).

Sub-Components:
- `outer loop`: A loop that iterates over the rows of the input matrices, with a loop counter `i` ranging from 0 to 63.
- `middle loop`: A loop that iterates over the columns of the input matrices, with a loop counter `j` ranging from 0 to 63.
- `inner loop`: A loop that performs the actual matrix multiplication, iterating over the elements of the input matrices and accumulating the products in a temporary variable `sum`.
- `matrix indexing`: A mechanism that calculates the memory addresses of the input and output matrices, using the loop counters `i`, `j`, and `k` to access the correct elements.