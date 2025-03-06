Kernel Description:
The `gradient_z_calc` kernel is designed to calculate the gradient in the z-direction of a 3D image. The kernel takes five 2D frames as input, each representing a different depth level of the image. The frames are processed pixel by pixel, and for each pixel, the kernel calculates the gradient in the z-direction using a weighted sum of the pixel values from the five input frames. The weights used are [1, -8, 0, 8, -1], which are applied to the corresponding frames in the order they are passed to the kernel. The weighted sum is then divided by 12 to obtain the final gradient value. The kernel uses fixed-point arithmetic, with the input frames represented as 17-bit fixed-point numbers with 9 bits of fractional precision, and the output gradient values represented as 32-bit fixed-point numbers with 13 bits of fractional precision.

The kernel iterates over each pixel in the input frames using two nested loops, one for the rows and one for the columns. For each pixel, the kernel calculates the gradient in the z-direction using the weighted sum of the pixel values from the five input frames. The result is then stored in the corresponding output array.

The kernel uses a simple and efficient algorithm to calculate the gradient in the z-direction, making it suitable for real-time image processing applications. The use of fixed-point arithmetic also makes the kernel suitable for implementation on hardware platforms that do not support floating-point arithmetic.

The kernel can be represented mathematically using the following equation:

$$
\begin{aligned}
G_z(x, y) &= \frac{1}{12} \left( f_1(x, y) - 8f_2(x, y) + 8f_4(x, y) - f_5(x, y) \right)
\end{aligned}
$$

where $G_z(x, y)$ is the gradient in the z-direction at pixel $(x, y)$, and $f_1(x, y)$, $f_2(x, y)$, $f_4(x, y)$, and $f_5(x, y)$ are the pixel values from the corresponding input frames.

---

Top-Level Function: `gradient_z_calc`

Complete Function Signature of the Top-Level Function:
`void gradient_z_calc(input_t frame1[MAX_HEIGHT][MAX_WIDTH], input_t frame2[MAX_HEIGHT][MAX_WIDTH], input_t frame3[MAX_HEIGHT][MAX_WIDTH], input_t frame4[MAX_HEIGHT][MAX_WIDTH], input_t frame5[MAX_HEIGHT][MAX_WIDTH], pixel_t gradient_z[MAX_HEIGHT][MAX_WIDTH]);`

Inputs:
- `frame1`: a 2D array of 17-bit fixed-point numbers with 9 bits of fractional precision, representing the first input frame.
- `frame2`: a 2D array of 17-bit fixed-point numbers with 9 bits of fractional precision, representing the second input frame.
- `frame3`: a 2D array of 17-bit fixed-point numbers with 9 bits of fractional precision, representing the third input frame.
- `frame4`: a 2D array of 17-bit fixed-point numbers with 9 bits of fractional precision, representing the fourth input frame.
- `frame5`: a 2D array of 17-bit fixed-point numbers with 9 bits of fractional precision, representing the fifth input frame.

Outputs:
- `gradient_z`: a 2D array of 32-bit fixed-point numbers with 13 bits of fractional precision, representing the gradient in the z-direction for each pixel in the input frames.

Important Data Structures and Data Types:
- `input_t`: a 17-bit fixed-point data type with 9 bits of fractional precision, used to represent the input frames.
- `pixel_t`: a 32-bit fixed-point data type with 13 bits of fractional precision, used to represent the output gradient values.

Sub-Components:
- None