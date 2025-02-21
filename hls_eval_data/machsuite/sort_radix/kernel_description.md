## sort_radix

An implementation of the radix sort approach to sort an array of integers. The algorithm is designed to be highly parallelizable and is optimized for execution on heterogeneous computing architectures. The kernel takes an input array `a` and sorts it in-place using a temporary buffer `b`. The sorting process is performed in multiple passes, with each pass sorting the array based on a specific radix (or digit) of the integers. The kernel uses a combination of local and global scans to efficiently sort the array.

Top-Level Function: `ss_sort`

Inputs:

- `a`: an array of `SIZE` integers to be sorted, where `SIZE` is 2048.
- `b`: a temporary array of `SIZE` integers used for sorting.
- `bucket`: an array of `BUCKETSIZE` integers used for storing the histogram of the input array, where `BUCKETSIZE` is `NUMOFBLOCKS*RADIXSIZE`.
- `sum`: an array of `SCAN_RADIX` integers used for storing the sum of the histogram.

Outputs:

- `a`: the sorted array of integers.

Important Data Structures and Data Types:

- `bucket`: an array of `BUCKETSIZE` integers used for storing the histogram of the input array. Each element of the array represents the count of integers in the input array that have a specific radix value.
- `sum`: an array of `SCAN_RADIX` integers used for storing the sum of the histogram. Each element of the array represents the cumulative sum of the counts in the `bucket` array.
- `TYPE`: an integer type defined as `int32_t`, used for representing the elements of the input array.
- `RADIXSIZE`: an integer constant defined as 4, representing the number of radix values used in the sorting process.

Sub-Components:

- `local_scan`: a function that performs a local scan of the `bucket` array to compute the cumulative sum of the counts.
- `sum_scan`: a function that performs a global scan of the `bucket` array to compute the sum of the histogram.
- `last_step_scan`: a function that updates the `bucket` array based on the sum of the histogram.
- `init`: a function that initializes the `bucket` array to zero.
- `hist`: a function that computes the histogram of the input array based on a specific radix value.
- `update`: a function that updates the input array based on the sorted histogram.