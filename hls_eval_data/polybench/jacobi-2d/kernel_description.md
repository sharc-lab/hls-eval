Kernel Description:
The `kernel_jacobi_2d` design is a high-level synthesis implementation of a Jacobi-style stencil computation over 2D data with a 5-point stencil pattern. The computation is simplified as taking the average of five points. The design iterates over a 2D grid of size 30x30, performing the stencil computation for a specified number of time steps (20 in this case). The computation is performed in a ping-pong fashion, alternating between two arrays `A` and `B`.

The stencil computation is performed according to the following equation:

$$
data^{t}_{(i,j)} = \frac{1}{5} \left( data^{t-1}_{(i,j)} + data^{t-1}_{(i-1,j)} + data^{t-1}_{(i+1,j)} + data^{t-1}_{(i,j-1)} + data^{t-1}_{(i,j+1)} \right)
$$

where `data` represents the input data, `t` represents the time step, and `(i,j)` represents the coordinates of the 2D grid.

The design uses a ping-pong approach, alternating between the `A` and `B` arrays, to perform the stencil computation. This approach allows for efficient use of memory and reduces the need for temporary storage.

---

Top-Level Function: `kernel_jacobi_2d`

Complete Function Signature of the Top-Level Function:
`void kernel_jacobi_2d(double A[30][30], double B[30][30]);`

Inputs:
- `A`: a 2D array of size 30x30, representing the input data for the stencil computation.
- `B`: a 2D array of size 30x30, representing the output data for the stencil computation.

Outputs:
- None

Important Data Structures and Data Types:
- `double [30][30]`: a 2D array of size 30x30, used to represent the input and output data for the stencil computation.

Sub-Components:
- None