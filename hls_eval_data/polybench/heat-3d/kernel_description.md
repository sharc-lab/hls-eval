Kernel Description:
The `kernel_heat_3d` design is a high-level synthesis implementation of the 3D heat equation algorithm. The algorithm updates the value of a 3D grid point based on the values of its neighboring points in the previous time step. The update equation is a discretized version of the heat equation, which describes how heat diffuses through a 3D space. The design consists of a nested loop structure that iterates over the 3D grid, updating the values of each point based on the values of its neighbors.

The main update is as follows:

$$
\begin{align*}
data^{t}_{(i,j,k)} = & \ data^{t-1}_{(i,j,k)} \\
& + 0.125 \cdot \left( data^{t-1}_{(i+1,j,k)} - 2 \cdot data^{t-1}_{(i,j,k)} + data^{t-1}_{(i-1,j,k)} \right) \\
& + 0.125 \cdot \left( data^{t-1}_{(i,j+1,k)} - 2 \cdot data^{t-1}_{(i,j,k)} + data^{t-1}_{(i,j-1,k)} \right) \\
& + 0.125 \cdot \left( data^{t-1}_{(i,j,k+1)} - 2 \cdot data^{t-1}_{(i,j,k)} + data^{t-1}_{(i,j,k-1)} \right)
\end{align*}
$$

The design assumes a fixed grid size of 10x10x10, and uses20 iterations, each containing two full grid sweeps (40 individual stencil advances). The input and output grids are represented as 3D arrays of doubles, with a size of 10x10x10. The design does not use any explicit data structures or sub-components beyond the top-level function.

---

Top-Level Function: `kernel_heat_3d`

Complete Function Signature of the Top-Level Function:
`void kernel_heat_3d(double A[10][10][10], double B[10][10][10]);`

Inputs:
- `A`: a 3D array of doubles, representing the input grid at the previous time step
- `B`: a 3D array of doubles, representing the output grid at the current time step

Outputs:
- `B`: the updated 3D grid at the current time step

Important Data Structures and Data Types:
- `double[10][10][10]`: a 3D array of doubles, representing the input and output grids

Sub-Components:
- None
Iteration/storage clarification: execute20 iterations. In each iteration first update every interior B[i][j][k] from the currently stored A using the displayed equation, then update every interior A[i][j][k] from the newly stored B using the same equation. Each sweep scans increasing i, then j, then k, with interior indices1..8. The complete first sweep finishes before the second starts. The native-double expression order is the three directional0.125-scaled second differences (i, then j, then k), followed by the center value. This describes40 stencil advances, not20 single advances.
Both A and B are observable mutable outputs after the20 pairs: A contains the result of the last second sweep and B the result of the last first sweep. For each array, all boundary faces preserve their own call-entry values. A and B must be distinct arrays; no inter-call state persists.
