Kernel Description:
The `flow_calc` kernel is designed to calculate the optical flow of a given input tensor. Optical flow is the pattern of apparent motion of objects, surfaces, and edges in a visual scene caused by the relative motion between an observer (an eye or a camera) and the scene. The kernel takes a 2D array of `tensor_t` structures as input, where each `tensor_t` represents a pixel in the input image. The `tensor_t` structure contains six `outer_pixel_t` values, which are used to calculate the optical flow at each pixel. The kernel outputs a 2D array of `velocity_t` structures, where each `velocity_t` represents the optical flow at the corresponding pixel in the input image.

The kernel uses a nested loop structure to iterate over each pixel in the input image. For each pixel, it calculates the optical flow using the values in the corresponding `tensor_t` structure. The calculation involves a series of arithmetic operations, including multiplications, subtractions, and divisions, which are performed using fixed-point arithmetic. The kernel uses a temporary buffer `buf` to store the intermediate results of the calculation.

The optical flow calculation is based on the following equations:

$$
u = \frac{t_6 \cdot t_4 - t_5 \cdot t_2}{t_1 \cdot t_2 - t_4 \cdot t_4}
$$

$$
v = \frac{t_5 \cdot t_4 - t_6 \cdot t_1}{t_1 \cdot t_2 - t_4 \cdot t_4}
$$

where $u$ and $v$ are the x and y components of the optical flow, and $t_1$ to $t_6$ are the values in the `tensor_t` structure.

The kernel handles the case where the denominator of the above equations is zero by setting the optical flow to zero. It also handles the case where the pixel is near the border of the image by setting the optical flow to zero.

---

Top-Level Function: `flow_calc`

Complete Function Signature of the Top-Level Function:
`void flow_calc(tensor_t tensors[MAX_HEIGHT][MAX_WIDTH], velocity_t outputs[MAX_HEIGHT][MAX_WIDTH]);`

Inputs:
- `tensors`: a 2D array of `tensor_t` structures, where each `tensor_t` represents a pixel in the input image. The `tensor_t` structure contains six `outer_pixel_t` values, which are used to calculate the optical flow at each pixel.

Outputs:
- `outputs`: a 2D array of `velocity_t` structures, where each `velocity_t` represents the optical flow at the corresponding pixel in the input image. The `velocity_t` structure contains two `vel_pixel_t` values, which represent the x and y components of the optical flow.

Important Data Structures and Data Types:
- `tensor_t`: a structure containing six `outer_pixel_t` values, which are used to calculate the optical flow at each pixel.
- `velocity_t`: a structure containing two `vel_pixel_t` values, which represent the x and y components of the optical flow.
- `outer_pixel_t`: a fixed-point data type with 32 bits and 13 fractional bits, used to represent the intermediate results of the calculation.
- `calc_pixel_t`: a fixed-point data type with 64 bits and 56 fractional bits, used to represent the values in the `tensor_t` structure.
- `vel_pixel_t`: a fixed-point data type with 32 bits and 13 fractional bits, used to represent the x and y components of the optical flow.

Sub-Components:
- None