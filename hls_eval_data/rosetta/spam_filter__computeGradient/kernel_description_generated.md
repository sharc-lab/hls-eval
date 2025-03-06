Kernel Description:
The computeGradient kernel is designed to compute the gradient of a given set of features. The gradient is calculated by multiplying each feature with a scale factor. The kernel is optimized for parallel execution, utilizing a loop unrolling factor of PAR_FACTOR to improve performance. The kernel operates on fixed-point numbers, with the feature and gradient values represented as ap_fixed<FTYPE_TWIDTH, FTYPE_IWIDTH> and the scale factor represented as ap_fixed<FTYPE_TWIDTH, FTYPE_IWIDTH>. The kernel's functionality can be represented by the equation: $grad_i = scale \times feature_i$, where $grad_i$ is the gradient of the $i^{th}$ feature, $scale$ is the scale factor, and $feature_i$ is the $i^{th}$ feature.

The kernel's architecture is designed to take advantage of the parallelism offered by the loop unrolling factor. The outer loop iterates over the features in blocks of size PAR_FACTOR, while the inner loop iterates over the features within each block. The kernel's dataflow is characterized by the cyclic partitioning of the grad and feature arrays, which allows for efficient parallel access to the data.

The kernel's implementation includes several important design decisions, including the use of fixed-point arithmetic and the loop unrolling factor. The fixed-point arithmetic is used to reduce the computational complexity and improve the performance of the kernel, while the loop unrolling factor is used to increase the parallelism and reduce the number of iterations.

The kernel's functionality can be represented by the following latex equation:
$grad = scale \times feature$, where $grad$ is the gradient vector, $scale$ is the scale factor, and $feature$ is the feature vector.

---

Top-Level Function: `computeGradient`

Complete Function Signature of the Top-Level Function:
`void computeGradient(FeatureType grad[NUM_FEATURES], DataType feature[NUM_FEATURES], FeatureType scale);`

Inputs:
- `grad`: an array of FeatureType values, representing the gradient of the features. The array has a size of NUM_FEATURES and is cyclically partitioned to allow for efficient parallel access.
- `feature`: an array of DataType values, representing the features. The array has a size of NUM_FEATURES and is cyclically partitioned to allow for efficient parallel access.
- `scale`: a FeatureType value, representing the scale factor.

Outputs:
- `grad`: the computed gradient of the features, stored in the input array.

Important Data Structures and Data Types:
- `FeatureType`: a fixed-point data type, represented as ap_fixed<FTYPE_TWIDTH, FTYPE_IWIDTH>, where FTYPE_TWIDTH is 32 and FTYPE_IWIDTH is 13.
- `DataType`: a fixed-point data type, represented as ap_fixed<DTYPE_TWIDTH, DTYPE_IWIDTH>, where DTYPE_TWIDTH is 16 and DTYPE_IWIDTH is 4.

Sub-Components:
- None