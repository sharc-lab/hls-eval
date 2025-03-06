Kernel Description:
The `clockwise_vertices` kernel is designed to reorder the vertices of a 2D triangle in a clockwise direction. The algorithm works by swapping the coordinates of the first and second vertices of the triangle. This is achieved through a series of temporary variable assignments, where the coordinates of the first vertex are stored in temporary variables, and then the coordinates of the second vertex are assigned to the first vertex. Finally, the coordinates stored in the temporary variables are assigned to the second vertex, effectively swapping the two vertices. The kernel assumes that the input triangle is represented by a `Triangle_2D` struct, which contains the x and y coordinates of the three vertices, as well as a z-coordinate, which is not modified by the kernel. The kernel does not perform any error checking or handling, and assumes that the input triangle is valid and properly formatted.

---

Top-Level Function: `clockwise_vertices`

Complete Function Signature of the Top-Level Function:
`void clockwise_vertices(Triangle_2D *triangle_2d);`

Inputs:
- `triangle_2d`: a pointer to a `Triangle_2D` struct, which represents the 2D triangle to be reordered. The struct contains the following fields:
  - `x0`, `y0`: the x and y coordinates of the first vertex, represented as 8-bit unsigned integers.
  - `x1`, `y1`: the x and y coordinates of the second vertex, represented as 8-bit unsigned integers.
  - `x2`, `y2`: the x and y coordinates of the third vertex, represented as 8-bit unsigned integers.
  - `z`: the z-coordinate of the triangle, represented as an 8-bit unsigned integer.

Outputs:
- None, the kernel modifies the input `triangle_2d` struct in-place.

Important Data Structures and Data Types:
- `Triangle_2D`: a struct representing a 2D triangle, containing the x and y coordinates of the three vertices, as well as a z-coordinate. The struct is composed of 8-bit unsigned integers, and is used as the input and output data structure for the kernel.
- `bit8`: an 8-bit unsigned integer type, used to represent the coordinates of the triangle vertices.

Sub-Components:
- None