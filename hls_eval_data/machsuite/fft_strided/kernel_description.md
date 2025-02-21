## fft_strided

An implementation of a FFT (Fast Fourier Transform) kernel based on the Cooley-Tukey algorithm, a divide-and-conquer approach to efficiently compute the discrete Fourier transform of a sequence. The design takes advantage of the strided memory access pattern to optimize data reuse and reduce memory bandwidth requirements. The kernel operates on complex-valued input data, represented as separate real and imaginary components, and produces the transformed output in the same format.

Top-Level Function: `fft`

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

- The outer loop (`outer`) iterates over the span of the input sequence, dividing it into smaller segments for processing.
- The inner loop (`inner`) iterates over the odd indices of the input sequence, performing the butterfly operation to combine adjacent elements.
- The twiddle factor multiplication component performs the complex multiplication of the input elements with the precomputed twiddle factors.