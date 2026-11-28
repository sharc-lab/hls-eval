Kernel Description:
The `check_clockwise` kernel is designed to determine the orientation of a 2D triangle, specifically whether its vertices are ordered in a clockwise or counterclockwise direction. This is achieved by calculating the cross product of two vectors formed by the triangle's vertices. The algorithm uses the shoelace formula, a mathematical algorithm to determine the orientation of a simple polygon whose vertices are given by their coordinates in the plane. In this case, the formula is applied to a triangle, which is a polygon with three vertices. The orientation is determined by the sign of the cross product, with its sign defined by the signed integer formula below, and zero indicating collinear vertices; no external Cartesian/screen-coordinate sign convention is imposed.

The kernel takes a `Triangle_2D` struct as input, which contains the coordinates of the triangle's vertices. The coordinates are represented as 8-bit unsigned integers (`bit8`). The kernel calculates the cross product using the following formula: 
\[ cw = (x_2 - x_0)(y_1 - y_0) - (y_2 - y_0)(x_1 - x_0) \]
where $(x_0, y_0)$, $(x_1, y_1)$, and $(x_2, y_2)$ are the coordinates of the triangle's vertices.

---

Top-Level Function: `check_clockwise`

Complete Function Signature of the Top-Level Function:
`int check_clockwise(Triangle_2D triangle_2d);`

Inputs:
- `triangle_2d`: a `Triangle_2D` struct containing the coordinates of the triangle's vertices, with fields:
  - `x0`: the x-coordinate of the first vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `y0`: the y-coordinate of the first vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `x1`: the x-coordinate of the second vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `y1`: the y-coordinate of the second vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `x2`: the x-coordinate of the third vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `y2`: the y-coordinate of the third vertex, represented as an 8-bit unsigned integer (`bit8`)
  - `z`: a reserved field, represented as an 8-bit unsigned integer (`bit8`)

Outputs:
- `cw`: an integer representing the orientation of the triangle, with its sign defined by the signed integer formula below, and zero indicating collinear vertices; no external Cartesian/screen-coordinate sign convention is imposed

Important Data Structures and Data Types:
- `Triangle_2D`: a struct representing a 2D triangle, with fields `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, and `z`, all represented as 8-bit unsigned integers (`bit8`)
- `bit8`: an 8-bit unsigned integer type, used to represent the coordinates of the triangle's vertices

Sub-Components:
- None

Numerical clarification: interpret each bit8 coordinate as its unsigned integer value in [0,255], then evaluate the stated subtractions and products as mathematical signed integers (the result fits int). Return the exact value of the displayed cw expression, not a sign-only code or modulo-AP subtraction. The reserved z field has no effect.
