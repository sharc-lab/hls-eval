Kernel Description:
The dotProduct kernel is designed to compute the dot product of two input vectors, `param` and `feature`, each of length `NUM_FEATURES`. The dot product is a fundamental operation in linear algebra, and it is used extensively in various fields such as machine learning, signal processing, and physics. The kernel takes advantage of the parallelism offered by the hardware to achieve high performance. The algorithm used in this kernel is a simple iterative approach, where each element of the `param` vector is multiplied with the corresponding element of the `feature` vector, and the results are accumulated to produce the final dot product. The kernel uses a technique called loop unrolling to improve performance, where the inner loop is unrolled by a factor of `PAR_FACTOR`. This allows the kernel to process `PAR_FACTOR` number of elements in parallel, resulting in a significant improvement in performance. The kernel also uses array partitioning to divide the input arrays into smaller blocks, which can be processed in parallel. The kernel is designed to work with fixed-point numbers, where the `param` vector is represented as a `FeatureType` and the `feature` vector is represented as a `DataType`. The `FeatureType` is a 32-bit fixed-point number with 13 integer bits and 19 fractional bits, while the `DataType` is a 16-bit fixed-point number with 4 integer bits and 12 fractional bits.

---

Top-Level Function: `dotProduct`

Complete Function Signature of the Top-Level Function:
`FeatureType dotProduct(FeatureType param[NUM_FEATURES], DataType feature[NUM_FEATURES]);`

Inputs:
- `param`: an array of `NUM_FEATURES` elements of type `FeatureType`, representing the first input vector.
- `feature`: an array of `NUM_FEATURES` elements of type `DataType`, representing the second input vector.

Outputs:
- `result`: a single value of type `FeatureType`, representing the dot product of the input vectors.

Important Data Structures and Data Types:
- `FeatureType`: a 32-bit fixed-point number with 13 integer bits and 19 fractional bits, used to represent the elements of the `param` vector.
- `DataType`: a 16-bit fixed-point number with 4 integer bits and 12 fractional bits, used to represent the elements of the `feature` vector.

Sub-Components:
- None