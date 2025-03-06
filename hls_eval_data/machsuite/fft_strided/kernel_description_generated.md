Kernel Description:
The FFT (Fast Fourier Transform) kernel is an implementation of the Cooley-Tukey algorithm, a divide-and-conquer approach to efficiently compute the discrete Fourier transform of a sequence. The design takes advantage of the strided memory access pattern to optimize data reuse and reduce memory bandwidth requirements. The kernel operates on complex-valued input data, represented as separate real and imaginary components, and produces the transformed output in the same format. The algorithm works by recursively dividing the input sequence into smaller segments, applying the butterfly operation to combine adjacent elements, and multiplying the results with precomputed twiddle factors. The twiddle factors are used to combine the results of the butterfly operations, and are computed based on the size of the input sequence. The kernel uses a 64-bit floating-point data type to represent the real and imaginary components of the input sequence and twiddle factors.

The high-level dataflow of the design involves the following steps:
1. The input sequence is divided into smaller segments, with each segment being processed independently.
2. The butterfly operation is applied to each segment, combining adjacent elements to produce a new set of elements.
3. The results of the butterfly operation are multiplied with the precomputed twiddle factors to produce the final transformed output.
4. The transformed output is stored in the same format as the input sequence, with the real and imaginary components represented as separate arrays.

The architecture of the design consists of a single kernel function, `fft`, which takes four input arrays: `real`, `img`, `real_twid`, and `img_twid`. The `real` and `img` arrays represent the real and imaginary components of the input sequence, respectively, while the `real_twid` and `img_twid` arrays represent the real and imaginary components of the twiddle factors, respectively. The kernel function operates on these input arrays, producing the transformed output in the same format.

The implementation of the kernel function involves two nested loops: an outer loop that iterates over the span of the input sequence, and an inner loop that iterates over the odd indices of the input sequence. The outer loop divides the input sequence into smaller segments, while the inner loop applies the butterfly operation to each segment. The results of the butterfly operation are multiplied with the precomputed twiddle factors, and the final transformed output is stored in the input arrays.

The kernel function uses a constant integer value, `FFT_SIZE`, to represent the size of the input sequence. This value is used to compute the twiddle factors and to divide the input sequence into smaller segments.

The design uses the following latex equation to represent the butterfly operation:
$$
\begin{bmatrix}
x_{even} \\
x_{odd}
\end{bmatrix}
=
\begin{bmatrix}
1 & 1 \\
1 & -1
\end{bmatrix}
\begin{bmatrix}
x_{even} \\
x_{odd}
\end{bmatrix}
$$
where $x_{even}$ and $x_{odd}$ represent the even and odd indices of the input sequence, respectively.

The design also uses the following latex equation to represent the twiddle factor multiplication:
$$
\begin{bmatrix}
x_{even} \\
x_{odd}
\end{bmatrix}
=
\begin{bmatrix}
1 & 0 \\
0 & W
\end{bmatrix}
\begin{bmatrix}
x_{even} \\
x_{odd}
\end{bmatrix}
$$
where $W$ represents the twiddle factor, and $x_{even}$ and $x_{odd}$ represent the even and odd indices of the input sequence, respectively.

---

Top-Level Function: `fft`

Complete Function Signature of the Top-Level Function:
`void fft(double real[FFT_SIZE], double img[FFT_SIZE], double real_twid[FFT_SIZE / 2], double img_twid[FFT_SIZE / 2]);`

Inputs:
- `real`: an array of `FFT_SIZE` (1024) `double` values representing the real component of the input sequence.
- `img`: an array of `FFT_SIZE` (1024) `double` values representing the imaginary component of the input sequence.
- `real_twid`: an array of `FFT_SIZE/2` (512) `double` values representing the real component of the twiddle factors.
- `img_twid`: an array of `FFT_SIZE/2` (512) `double` values representing the imaginary component of the twiddle factors.

Outputs:
- The transformed real and imaginary components are stored in the input arrays `real` and `img`, respectively.

Important Data Structures and Data Types:
- `double`: a 64-bit floating-point data type used to represent the real and imaginary components of the input sequence and twiddle factors.
- `FFT_SIZE`: a constant integer value (1024) representing the size of the input sequence.

Sub-Components:
- `outer`: the outer loop that iterates over the span of the input sequence, dividing it into smaller segments for processing.
    - Signature: `for (span = FFT_SIZE >> 1; span; span >>= 1, log++)`
    - Details: The outer loop is used to divide the input sequence into smaller segments, with each segment being processed independently.
- `inner`: the inner loop that iterates over the odd indices of the input sequence, applying the butterfly operation to combine adjacent elements.
    - Signature: `for (odd = span; odd < FFT_SIZE; odd++)`
    - Details: The inner loop is used to apply the butterfly operation to each segment of the input sequence, combining adjacent elements to produce a new set of elements.
- `twiddle factor multiplication`: the component that performs the complex multiplication of the input elements with the precomputed twiddle factors.
    - Signature: `temp = real_twid[rootindex] * real[odd] - img_twid[rootindex] * img[odd];`
    - Details: The twiddle factor multiplication component is used to combine the results of the butterfly operation with the precomputed twiddle factors, producing the final transformed output.