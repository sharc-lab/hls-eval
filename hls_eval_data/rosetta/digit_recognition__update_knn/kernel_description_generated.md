Kernel Description:
The `update_knn` kernel is designed to update the k-nearest neighbors (KNN) for a given test instance. The kernel takes in a test instance and a training instance, both represented as 256-bit unsigned integers (`WholeDigitType`), and an array of minimum distances (`min_distances`) of size `K_CONST`. The kernel calculates the Hamming distance between the test instance and the training instance using the XOR operation and the `popcount` function, which counts the number of set bits in the resulting difference. The kernel then finds the maximum distance in the `min_distances` array and replaces it with the newly calculated distance if it is smaller. This process is repeated for each training instance to update the KNN for the test instance. The kernel uses a simple iterative approach to find the maximum distance, which is suitable for implementation on an FPGA.

The `popcount` function is a crucial component of the kernel, which counts the number of set bits in a given 256-bit unsigned integer. This function is implemented using a straightforward iterative approach, which is efficient on an FPGA. The kernel also uses a loop to find the maximum distance in the `min_distances` array, which has a fixed size of `K_CONST`.

The kernel's functionality can be represented by the following equation:
\[ dist = \sum_{i=0}^{255} (test\_inst[i] \oplus train\_inst[i]) \]
where $dist$ is the Hamming distance between the test instance and the training instance, and $\oplus$ represents the bitwise XOR operation.

---

Top-Level Function: `update_knn`

Complete Function Signature of the Top-Level Function:
`void update_knn(WholeDigitType test_inst, WholeDigitType train_inst, int min_distances[K_CONST]);`

Inputs:
- `test_inst`: a 256-bit unsigned integer representing the test instance.
- `train_inst`: a 256-bit unsigned integer representing the training instance.
- `min_distances`: an array of integers of size `K_CONST` representing the minimum distances.

Outputs:
- None (the kernel updates the `min_distances` array in-place).

Important Data Structures and Data Types:
- `WholeDigitType`: a 256-bit unsigned integer type used to represent the test and training instances.
- `min_distances`: an array of integers of size `K_CONST` used to store the minimum distances.

Sub-Components:
- `popcount`:
    - Signature: `int popcount(WholeDigitType x);`
    - Details: a function that counts the number of set bits in a given 256-bit unsigned integer. This function is used to calculate the Hamming distance between the test instance and the training instance.