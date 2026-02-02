Kernel Description:
The `ss_sort` kernel implements the radix sort algorithm, a highly parallelizable sorting technique optimized for execution on heterogeneous computing architectures. The algorithm sorts an array of integers in-place using a temporary buffer. The sorting process is performed in multiple passes, with each pass sorting the array based on a specific radix (or digit) of the integers. The kernel utilizes a combination of local and global scans to efficiently sort the array.

The radix sort algorithm works by iterating over each digit position in the integers, starting from the least significant digit. For each digit position, the algorithm computes a histogram of the input array, where each bin in the histogram corresponds to a specific radix value. The histogram is then used to determine the final position of each integer in the sorted array.

The `ss_sort` kernel uses several key data structures to implement the radix sort algorithm. The `bucket` array stores the histogram of the input array, where each element represents the count of integers with a specific radix value. The `sum` array stores the cumulative sum of the histogram, which is used to determine the final position of each integer in the sorted array.

The kernel consists of several sub-components, each responsible for a specific step in the radix sort algorithm. The `init` function initializes the `bucket` array to zero, while the `hist` function computes the histogram of the input array for a given digit position. The `local_scan` function performs a local scan of the `bucket` array to compute the cumulative sum of the counts, and the `sum_scan` function performs a global scan of the `bucket` array to compute the sum of the histogram. The `last_step_scan` function updates the `bucket` array based on the sum of the histogram, and the `update` function updates the input array based on the sorted histogram.

The `ss_sort` kernel takes four inputs: `a` and `b`, which are the input and temporary arrays, respectively; `bucket`, which is the histogram array; and `sum`, which is the cumulative sum array. The kernel produces one output: the sorted array `a`.

The kernel uses several key constants to control the sorting process. The `SIZE` constant defines the size of the input array, while the `NUMOFBLOCKS` constant defines the number of blocks in the input array. The `ELEMENTSPERBLOCK` constant defines the number of elements per block, and the `RADIXSIZE` constant defines the number of radix values used in the sorting process.

The kernel also uses several key equations to implement the radix sort algorithm. The histogram computation is based on the equation: $bucket[(a[i] >> exp) & 0x3]++$, where $a[i]$ is the $i^{th}$ element of the input array, $exp$ is the current digit position, and $bucket$ is the histogram array. The cumulative sum computation is based on the equation: $sum[i] = sum[i-1] + bucket[i-1]$, where $sum$ is the cumulative sum array and $bucket$ is the histogram array.

---

Top-Level Function: `ss_sort`

Complete Function Signature of the Top-Level Function:
`void ss_sort(int a[SIZE], int b[SIZE], int bucket[BUCKETSIZE], int sum[SCAN_RADIX]);`

Inputs:
- `a`: an array of `SIZE` integers to be sorted, where `SIZE` is 2048. The array is stored in row-major order, with each element represented as a 32-bit integer.
- `b`: a temporary array of `SIZE` integers used for sorting. The array is stored in row-major order, with each element represented as a 32-bit integer.
- `bucket`: an array of `BUCKETSIZE` integers used for storing the histogram of the input array, where `BUCKETSIZE` is `NUMOFBLOCKS*RADIXSIZE`. The array is stored in row-major order, with each element represented as a 32-bit integer.
- `sum`: an array of `SCAN_RADIX` integers used for storing the sum of the histogram. The array is stored in row-major order, with each element represented as a 32-bit integer.

Outputs:
- `a`: the sorted array of integers.

Important Data Structures and Data Types:
- `bucket`: an array of `BUCKETSIZE` integers used for storing the histogram of the input array. Each element of the array represents the count of integers in the input array that have a specific radix value.
- `sum`: an array of `SCAN_RADIX` integers used for storing the sum of the histogram. Each element of the array represents the cumulative sum of the counts in the `bucket` array.
- `TYPE`: an integer type defined as `int32_t`, used for representing the elements of the input array.
- `RADIXSIZE`: an integer constant defined as 4, representing the number of radix values used in the sorting process.

Sub-Components:
- `local_scan`:
    - Signature: `void local_scan(int bucket[BUCKETSIZE]);`
    - Details: The `local_scan` function performs a local scan of the `bucket` array to compute the cumulative sum of the counts. The function iterates over each block in the `bucket` array and computes the cumulative sum of the counts in that block.
- `sum_scan`:
    - Signature: `void sum_scan(int sum[SCAN_RADIX], int bucket[BUCKETSIZE]);`
    - Details: The `sum_scan` function performs a global scan of the `bucket` array to compute the sum of the histogram. The function iterates over each block in the `bucket` array and computes the sum of the counts in that block.
- `last_step_scan`:
    - Signature: `void last_step_scan(int bucket[BUCKETSIZE], int sum[SCAN_RADIX]);`
    - Details: The `last_step_scan` function updates the `bucket` array based on the sum of the histogram. The function iterates over each block in the `bucket` array and updates the counts in that block based on the sum of the histogram.
- `init`:
    - Signature: `void init(int bucket[BUCKETSIZE]);`
    - Details: The `init` function initializes the `bucket` array to zero. The function iterates over each element in the `bucket` array and sets it to zero.
- `hist`:
    - Signature: `void hist(int bucket[BUCKETSIZE], int a[SIZE], int exp);`
    - Details: The `hist` function computes the histogram of the input array for a given digit position. The function iterates over each element in the input array and increments the corresponding bin in the `bucket` array based on the digit value at the current position.
- `update`:
    - Signature: `void update(int b[SIZE], int bucket[BUCKETSIZE], int a[SIZE], int exp);`
    - Details: The `update` function updates the input array based on the sorted histogram. The function iterates over each element in the input array and updates its position in the output array based on the sorted histogram.