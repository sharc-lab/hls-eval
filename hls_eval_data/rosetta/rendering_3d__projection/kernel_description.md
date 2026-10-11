Kernel Description:
The kernel performs an orthographic coordinate-plane projection of a triangle for angle0,1 or2. It does not perform perspective division. For angle0, projected(x,y)=(original x,original y) and depth uses original z. For angle1, projected(x,y)=(original x,original z) and depth uses original y. For angle2, projected(x,y)=(original z,original y) and depth uses original x. Copy each vertex coordinate into its corresponding output field. The shared output z is floor((depth0+depth1+depth2)/3), computing the sum in a type wide enough to hold765 before division; do not wrap the sum to bit8 or truncate each depth before adding. Inputs span the full unsigned bit8 range, including zero; angle must be0,1 or2. All seven Triangle_2D fields are outputs and all are overwritten; no prior output value is used.

---

Top-Level Function: `projection`

Complete Function Signature of the Top-Level Function:
`void projection(Triangle_3D triangle_3d, Triangle_2D *triangle_2d, bit2 angle);`

Inputs:
- `triangle_3d`: a 3D triangle defined by its three vertices, each with x, y, and z coordinates, represented as a `Triangle_3D` struct.
- `triangle_2d`: a pointer to a 2D triangle that will store the projected result, represented as a `Triangle_2D` struct.
- `angle`: the angle of projection, represented as a `bit2` value, which can be 0, 1, or 2.

Outputs:
- `triangle_2d`: the projected 2D triangle, with its vertices' x and y coordinates calculated based on the 3D triangle's vertices and the angle of projection, and its z coordinate calculated by the angle-selected depth rule above.

Important Data Structures and Data Types:
- `Triangle_3D`: a struct representing a 3D triangle, with fields `x0`, `y0`, `z0`, `x1`, `y1`, `z1`, `x2`, `y2`, and `z2`, each of type `bit8`.
- `Triangle_2D`: a struct representing a 2D triangle, with fields `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, and `z`, each of type `bit8`.
- `bit2`: an unsigned 2-bit integer type, used to represent the angle of projection.
- `bit8`: an unsigned 8-bit integer type, used to represent the coordinates of the 3D and 2D triangles.

Sub-Components:
- None