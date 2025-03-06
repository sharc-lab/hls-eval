Kernel Description:
The `outer_product` kernel computes the outer product of a 3D vector for each pixel in a 2D grid. The input is a 2D array of vectors, where each vector has three components (x, y, z). The output is a 2D array of 6-element vectors, where each element of the output vector is the result of specific pairwise multiplications of the input vector components. The specific multiplications are: \(x \times x\), \(y \times y\), \(z \times z\), \(x \times y\), \(x \times z\), and \(y \times z\). The kernel iterates over each pixel in the input grid, performs the required multiplications, and stores the results in the corresponding position in the output grid. The use of fixed-point arithmetic (`ap_fixed`) ensures precision and control over the bit-width and fractional part of the numbers, which is crucial for hardware synthesis.

The kernel is designed to handle a grid of size `MAX_HEIGHT` x `MAX_WIDTH`, with `MAX_HEIGHT` set to 436 and `MAX_WIDTH` set to 1024. The input vectors are of type `gradient_t`, which contains three `pixel_t` components. The output vectors are of type `outer_t`, which contains six `outer_pixel_t` components. The kernel uses nested loops to iterate over the grid, with the outer loop iterating over the rows and the inner loop iterating over the columns. Each iteration computes the outer product for a single pixel and stores the result in the output grid.

---

Top-Level Function: `outer_product`

Complete Function Signature of the Top-Level Function:
`void outer_product(gradient_t gradient[MAX_HEIGHT][MAX_WIDTH], outer_t outer_product[MAX_HEIGHT][MAX_WIDTH]);`

Inputs:
- `gradient`: A 2D array of `gradient_t` structures, representing the input vectors. Each `gradient_t` contains three `pixel_t` components (x, y, z). The array dimensions are `MAX_HEIGHT` x `MAX_WIDTH`.

Outputs:
- `outer_product`: A 2D array of `outer_t` structures, representing the computed outer products. Each `outer_t` contains six `outer_pixel_t` components, which are the results of the pairwise multiplications of the input vector components. The array dimensions are `MAX_HEIGHT` x `MAX_WIDTH`.

Important Data Structures and Data Types:
- `gradient_t`: A structure containing three `pixel_t` components (x, y, z). Used to represent the input vectors.
- `outer_t`: A structure containing six `outer_pixel_t` components. Used to represent the output vectors.
- `pixel_t`: A fixed-point data type (`ap_fixed<32, 13>`) representing the components of the input vectors.
- `outer_pixel_t`: A fixed-point data type (`ap_fixed<32, 27>`) representing the components of the output vectors.

Sub-Components:
- None