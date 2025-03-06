Kernel Description:
The projection kernel is designed to project a 3D triangle onto a 2D plane. The kernel takes into account the angle of projection, which can be one of three possible values: 0, 1, or 2. The 3D triangle is defined by its three vertices, each with x, y, and z coordinates. The 2D triangle is defined by its three vertices, each with x and y coordinates, and a z coordinate that represents the average z value of the 3D triangle's vertices. The kernel uses a simple projection algorithm, where the x and y coordinates of the 2D triangle's vertices are calculated based on the x, y, and z coordinates of the 3D triangle's vertices and the angle of projection. The z coordinate of the 2D triangle is calculated as the average of the z coordinates of the 3D triangle's vertices. The kernel assumes that the camera is located at (0,0,-1) and the canvas is at the z=0 plane, with the 3D model lying in the z>0 space. The coordinate on the canvas is proportional to the corresponding coordinate in space.

---

Top-Level Function: `projection`

Complete Function Signature of the Top-Level Function:
`void projection(Triangle_3D triangle_3d, Triangle_2D *triangle_2d, bit2 angle);`

Inputs:
- `triangle_3d`: a 3D triangle defined by its three vertices, each with x, y, and z coordinates, represented as a `Triangle_3D` struct.
- `triangle_2d`: a pointer to a 2D triangle that will store the projected result, represented as a `Triangle_2D` struct.
- `angle`: the angle of projection, represented as a `bit2` value, which can be 0, 1, or 2.

Outputs:
- `triangle_2d`: the projected 2D triangle, with its vertices' x and y coordinates calculated based on the 3D triangle's vertices and the angle of projection, and its z coordinate calculated as the average of the 3D triangle's vertices' z coordinates.

Important Data Structures and Data Types:
- `Triangle_3D`: a struct representing a 3D triangle, with fields `x0`, `y0`, `z0`, `x1`, `y1`, `z1`, `x2`, `y2`, and `z2`, each of type `bit8`.
- `Triangle_2D`: a struct representing a 2D triangle, with fields `x0`, `y0`, `x1`, `y1`, `x2`, `y2`, and `z`, each of type `bit8`.
- `bit2`: an unsigned 2-bit integer type, used to represent the angle of projection.
- `bit8`: an unsigned 8-bit integer type, used to represent the coordinates of the 3D and 2D triangles.

Sub-Components:
- None