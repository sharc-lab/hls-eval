Kernel Description:
The `kernel_jacobi_1d` design is a high-level synthesis implementation of a Jacobi-style stencil computation over 1D data with a 3-point stencil pattern. The algorithm iteratively updates the input data by taking the average of three neighboring points. The computation is performed in a time-stepped manner, where each time step updates the entire data array.

The algorithm can be mathematically represented as:

$$
data^{t}_{(i)} = \frac{1}{3} \left( data^{t-1}_{(i)} + data^{t-1}_{(i-1)} + data^{t-1}_{(i+1)} \right)
$$

where $data^{t}_{(i)}$ represents the value at index $i$ at time step $t$, and $data^{t-1}_{(i)}$ represents the value at index $i$ at the previous time step.

Note that the design assumes a fixed size of 30 for the input and output arrays, and a fixed number of time steps (20). These values can be adjusted by modifying the constants `n` and `tsteps` in the design.

---

Top-Level Function: `kernel_jacobi_1d`

Complete Function Signature of the Top-Level Function:
`void kernel_jacobi_1d(double A[30], double B[30]);`

Inputs:
- `A`: a 1D array of 30 `double` values, representing the input data at the previous time step.
- `B`: a 1D array of 30 `double` values, representing the output data at the current time step.

Outputs:
- `A`: the updated input data at the current time step.
- `B`: the output data at the current time step.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the input and output data.

Sub-Components:
- None