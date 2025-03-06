Kernel Description:
The `stencil3d` kernel implements a 3D stencil computation algorithm, which is a common technique used in various scientific simulations, such as fluid dynamics, heat transfer, and image processing. The algorithm applies a weighted sum of neighboring elements to each element in a 3D array, using a set of coefficients to determine the weights. The kernel also handles boundary conditions by filling the output array with original values at the boundaries.

The kernel takes a 3D array of input values, applies the stencil operation to each element, and produces a 3D array of output values. The stencil operation involves computing a weighted sum of neighboring elements, where the weights are stored in a coefficient array. The kernel uses a set of nested loops to iterate over the elements of the input array, applying the stencil operation to each element and storing the result in the output array.

The kernel uses the following equation to compute the output value for each element:
\[ sol[i, j, k] = C[0] \times orig[i, j, k] + C[1] \times (orig[i, j, k+1] + orig[i, j, k-1] + orig[i, j+1, k] + orig[i, j-1, k] + orig[i+1, j, k] + orig[i-1, j, k]) \]
where $sol[i, j, k]$ is the output value at position $(i, j, k)$, $C[0]$ and $C[1]$ are the coefficients, and $orig[i, j, k]$ is the input value at position $(i, j, k)$.

The kernel handles boundary conditions by filling the output array with original values at the boundaries. This is done using a set of nested loops that iterate over the elements of the input array, checking if the current element is at the boundary. If it is, the kernel sets the corresponding output value to the original input value.

The kernel uses a set of macros to define the input sizes, data bounds, and convenience functions. The `SIZE` macro defines the total size of the 3D array, computed as `row_size * col_size * height_size`. The `INDX` macro defines a convenience function to compute the index of an element in the 3D array, given its row, column, and height indices.

---

Top-Level Function: `stencil3d`

Complete Function Signature of the Top-Level Function:
`void stencil3d(TYPE C[2], TYPE orig[SIZE], TYPE sol[SIZE]);`

Inputs:
- `C`: a 1D array of two coefficients, `C[0]` and `C[1]`, of type `int32_t`, used for weighting the stencil operation.
- `orig`: a 3D array of input values, of size `SIZE` (row_size x col_size x height_size), of type `int32_t`, representing the original data.
- `sol`: a 3D array of output values, of size `SIZE` (row_size x col_size x height_size), of type `int32_t`, representing the solution.

Outputs:
- `sol`: the 3D array of output values, of size `SIZE` (row_size x col_size x height_size), of type `int32_t`, representing the solution.

Important Data Structures and Data Types:
- `TYPE`: an alias for `int32_t`, used to represent the data type of the input and output arrays.
- `SIZE`: a constant representing the total size of the 3D array, computed as `row_size * col_size * height_size`.
- `INDX`: a macro used to compute the index of an element in the 3D array, given its row, column, and height indices.

Sub-Components:
- `Boundary condition handling`: a set of nested loops that fill the output array with original values at the boundaries.
- `Stencil computation`: a set of nested loops that apply the stencil operation to each element of the input array, using the coefficient array and the original values.