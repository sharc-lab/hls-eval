Kernel Description:
The outer product kernel is designed to compute the outer product of a 3D gradient vector. The kernel takes a 2D array of gradient vectors as input, where each gradient vector is represented by three components (x, y, z). The outer product is computed for each gradient vector, resulting in a 2D array of outer product tensors. Each outer product tensor is a 6-element vector, where the elements are the products of the corresponding components of the gradient vector. The kernel uses a nested loop structure to iterate over the input gradient vectors, computing the outer product for each vector and storing the result in the output array.

The outer product computation can be represented mathematically as follows:
Let $g = (x, y, z)$ be a 3D gradient vector. The outer product of $g$ is a 6-element vector $o = (x^2, y^2, z^2, xy, xz, yz)$. This computation is performed for each gradient vector in the input array, resulting in a 2D array of outer product tensors.

The kernel uses fixed-point arithmetic to represent the input and output data. The input gradient vectors are represented using the `gradient_t` struct, which consists of three `pixel_t` components. The output outer product tensors are represented using the `outer_t` struct, which consists of six `outer_pixel_t` components.

---

Top-Level Function: `outer_product`

Complete Function Signature of the Top-Level Function:
`void outer_product(gradient_t gradient[MAX_HEIGHT][MAX_WIDTH], outer_t outer_product[MAX_HEIGHT][MAX_WIDTH]);`

Inputs:
- `gradient`: a 2D array of `gradient_t` structs, representing the input gradient vectors. Each `gradient_t` struct consists of three `pixel_t` components (x, y, z).
- `MAX_HEIGHT` and `MAX_WIDTH`: constants representing the height and width of the input array, respectively.

Outputs:
- `outer_product`: a 2D array of `outer_t` structs, representing the output outer product tensors. Each `outer_t` struct consists of six `outer_pixel_t` components.

Important Data Structures and Data Types:
- `gradient_t`: a struct representing a 3D gradient vector, consisting of three `pixel_t` components (x, y, z).
- `outer_t`: a struct representing an outer product tensor, consisting of six `outer_pixel_t` components.
- `pixel_t`: a fixed-point data type representing a single component of a gradient vector, with 32 bits and 13 fractional bits.
- `outer_pixel_t`: a fixed-point data type representing a single component of an outer product tensor, with 32 bits and 27 fractional bits.

Sub-Components:
- None